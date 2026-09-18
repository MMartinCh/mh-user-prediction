from pathlib import Path
from config.config_loader import ConfigLoader

def test_load_config(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
        model:
          type: RandomForestRegressor
          n_estimators: 200
          max_depth: 10

        scraper:
          web_settings:
            overwrite: false
            polite_delay: 1.0
            timeout: 10.0
            user_agent: "user_agent_string"

          ranking:
            url: https://example.com/ranking
            cache: data/ranking.csv
            overwrite: false

          wiki:
            url: https://example.com/wiki
            cache: data/wiki.csv
            overwrite: false
            utils:
              monster_links: /data/utils/wiki_links.txt

          quest:
            cache: data/quest.csv
            partial:
              world:
                game: Monster Hunter World
                generation: 5
                cache: data/world.json
                utils:
                  monster_data: data/world_monsters.json
                overwrite: false
            overwrite: false

        paths:
          data_path: data
          metadata_path: metadata.yaml
        """,
        encoding="utf-8",
    )

    config = ConfigLoader(config_file).load()

    assert config.model.type == "RandomForestRegressor"
    assert config.model.n_estimators == 200
    assert config.scraper.web_settings.polite_delay == 1.0
    assert config.scraper.ranking.url == "https://example.com/ranking"
    assert config.scraper.quest.partial["world"].game == "Monster Hunter World"
    assert config.scraper.quest.partial["world"].generation == 5