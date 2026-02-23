"""Deploy the character agent to Vertex AI Agent Engine.

このスクリプトは FastAPI の起動とは独立したスタンドアロンスクリプトです。
エージェントコードが変更された場合にのみ実行してください。

Usage:
    # プロジェクトルートから実行
    uv run python scripts/deploy_agent.py          # 初回デプロイ
    uv run python scripts/deploy_agent.py --update # コード変更後の再デプロイ
"""

import argparse
import json
import sys
from pathlib import Path

# スタンドアロン実行時に backend/ をパスに追加
_BACKEND_PATH = Path(__file__).parent.parent / "backend"
if str(_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PATH))

import vertexai
from vertexai.agent_engines import AdkApp

from app.core.config import get_settings
from app.models.image import CharacterConfig
from app.services.agent import build_agent
from app.services.agent_tools import initialize_session, save_to_memory, update_affinity

# Agent Engine へのデプロイに必要なパッケージ
REQUIREMENTS = [
    "google-cloud-aiplatform[agent_engines,adk]",
    "google-cloud-firestore",
]

_CHARACTER_JSON_PATH = Path(__file__).parent.parent / "data" / "characters" / "character.json"


def load_character_config() -> CharacterConfig:
    """data/characters/character.json からキャラクター設定を読み込む。

    Returns:
        CharacterConfig インスタンス。
    """
    with open(_CHARACTER_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return CharacterConfig(**data)


def deploy(update: bool = False) -> None:
    """エージェントを Agent Engine にデプロイまたは更新する。

    Args:
        update: True の場合、既存デプロイを更新する（コード変更後の再デプロイ）。
                False の場合（デフォルト）、新規デプロイを実行する。
    """
    settings = get_settings()

    vertexai.init(
        project=settings.gcp_project_id,
        location=settings.vertex_ai_location,
        staging_bucket=settings.staging_bucket or None,
    )

    character_config = load_character_config()
    agent = build_agent(
        character_config=character_config,
        extra_tools=[initialize_session, update_affinity, save_to_memory],
    )
    app = AdkApp(agent=agent)

    if update:
        # コード変更後の再デプロイ
        existing = vertexai.agent_engines.get(settings.agent_engine_id)
        existing.update(app)
        print(f"Updated Agent Engine: {settings.agent_engine_id}")
    else:
        # 初回デプロイ
        deployed = vertexai.agent_engines.create(app, requirements=REQUIREMENTS)
        agent_engine_id = deployed.resource_name.split("/")[-1]
        print(f"Deployed Agent Engine ID: {agent_engine_id}")
        print(f".env を更新してください: AGENT_ENGINE_ID={agent_engine_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Vertex AI Agent Engine へキャラクターエージェントをデプロイします。"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="既存のデプロイを更新します（コード変更後に使用）。",
    )
    args = parser.parse_args()
    deploy(update=args.update)
