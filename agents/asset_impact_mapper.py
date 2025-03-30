import json
import logging
import re
import copy
from core.llm_interface import call_gpt
from core.agent_runner import AgentRunner
from utils.prompt_loader import load_prompt


class AssetImpactMapperAgent(AgentRunner):
    def __init__(self):
        prompt = load_prompt("asset_impact_mapper")
        super().__init__(prompt)
        self.summary = ""

    async def run(self, belief_state: dict, input_data: str = None) -> dict:
        grounded_events = belief_state.get("event_branches", [])
        mapped_assets = belief_state.get("mapped_assets", [])

        # Create a set of unique event-to-asset mappings
        existing_signatures = {
            self._mapping_signature(entry) for entry in mapped_assets
        }

        new_assets = []

        for event in grounded_events:
            if event.get("analyzed"):
                continue

            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": json.dumps(event)}
            ]

            try:
                raw_response = await call_gpt(messages)
                logging.debug(
                    f"AssetImpactMapperAgent raw response: {raw_response}")

                repaired = self._try_json_repair(raw_response.strip())
                asset_links = json.loads(repaired)

                for item in asset_links:
                    enriched_item = copy.deepcopy(item)
                    enriched_item["event"] = event["event"]
                    enriched_item["date"] = event.get("date")
                    enriched_item["analyzed"] = False

                    signature = self._mapping_signature(enriched_item)
                    if signature not in existing_signatures:
                        new_assets.append(enriched_item)
                        existing_signatures.add(signature)

                event["analyzed"] = True

            except Exception as e:
                logging.warning(
                    f"AssetImpactMapperAgent: Failed to map assets. {str(e)}")
                logging.debug(f"Raw GPT response:\n{raw_response}")
                continue

        mapped_assets += new_assets
        belief_state["mapped_assets"] = mapped_assets
        self.summary = f"AssetImpactMapper: Mapped {len(new_assets)} new assets (total: {len(mapped_assets)})."
        return belief_state

    def _mapping_signature(self, item: dict) -> str:
        """Create a unique signature for a mapping to avoid duplicates."""
        return json.dumps({
            "event": item.get("event"),
            "ticker": item.get("ticker"),
            "date": item.get("date")
        }, sort_keys=True)

    def _try_json_repair(self, raw_text: str) -> str:
        try:
            match = re.search(r"\[(?:.|\n)*?\]", raw_text)
            if match:
                raw_text = match.group(0)
            else:
                raise ValueError("No JSON array found in response.")

            cleaned = raw_text
            cleaned = cleaned.replace('“', '"').replace('”', '"')
            cleaned = cleaned.replace("’", "'").replace("‘", "'")
            cleaned = cleaned.replace("–", "-").replace("—", "-")
            cleaned = cleaned.replace("…", "...").replace("•", "-")
            cleaned = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", cleaned)

            cleaned = re.sub(
                r'"rationale"\s*:\s*"([^"]*?)"',
                lambda m: '"rationale": "{}"'.format(
                    m.group(1).replace('"', '\\"')),
                cleaned
            )

            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

            return cleaned.strip()
        except Exception as e:
            logging.warning(
                "AssetImpactMapperAgent: JSON repair failed: %s", str(e))
            return raw_text
