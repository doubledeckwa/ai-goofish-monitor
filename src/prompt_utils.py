import asyncio
import json
import os
import sys

import aiofiles

from src.infrastructure.external.ai_client import AIClient

# The meta-prompt to instruct the AI
META_PROMPT_TEMPLATE = """
you are a world classAIPrompt Word Engineering Master. Your tasks are based on what the user provides【Purchase demand], imitate a【Reference example], for the Xianyu monitoring robotAIAnalysis module (codename EagleEye）Generate a new [analysis standard】text。

Your output must strictly follow [Reference Example】The structure, tone and core principles of，However, the content must be completely targeted at users’ [purchasing needs]】Customize. The final generated text will be asAIThinking Guide for the Analysis Module。

---
This is [reference example】（`macbook_criteria.txt`）：
```text
{reference_text}
```
---

This is the user’s [purchase demand]】：
```text
{user_description}
```
---

Please start generating new [Analysis Standards] now】text. please note：
1.  **Only output the newly generated text content**，Do not include any additional explanations, titles, or code block tags。
2.  Keep the example `[V6.3 Core upgrade]`、`[V6.4 logic correction]` etc. version marking, which helps maintain formatting consistency。
3.  Replace everything in the example with "MacBook" Relevant content is replaced with content related to the products the user needs.。
4.  Think about and generate "one-vote veto" rules for new product types”and “Red Flag Checklist.”。
"""


async def generate_criteria(user_description: str, reference_file_path: str) -> str:
    """
    Generates a new criteria file content using AI.
    """
    ai_client = AIClient()
    if not ai_client.is_available():
        ai_client.refresh()
    if not ai_client.is_available():
        raise RuntimeError("AIThe client is not initialized and cannot generate analysis standards.。Check, please.envConfiguration。")

    print(f"Reading reference file: {reference_file_path}")
    try:
        with open(reference_file_path, 'r', encoding='utf-8') as f:
            reference_text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Reference file not found: {reference_file_path}")
    except IOError as e:
        raise IOError(f"Failed to read reference file: {e}")

    print("Building is being sent toAIinstructions...")
    prompt = META_PROMPT_TEMPLATE.format(
        reference_text=reference_text,
        user_description=user_description
    )

    print("CallingAIGenerating new analysis standards, please wait....")
    try:
        request_params = {
            "model": ai_client.settings.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
        }
        if ai_client.settings.enable_thinking:
            request_params["extra_body"] = {"enable_thinking": False}

        response = await ai_client.client.chat.completions.create(**request_params)
        # Compatible with differentAPIresponse format, checkresponseWhether it is a string
        if hasattr(response, 'choices'):
            generated_text = response.choices[0].message.content
        else:
            # ifresponseis a string, use it directly
            generated_text = response
        print("AIContent generated successfully。")
        
        # deal withcontentmay beNoneOr the case of empty string
        if generated_text is None or generated_text.strip() == "":
            raise RuntimeError("AIThe returned content is empty, please check the model configuration or try again。")
        
        return generated_text.strip()
    except Exception as e:
        print(f"call OpenAI API error: {e}")
        raise e


async def update_config_with_new_task(new_task: dict, config_file: str = "config.json"):
    """
    Adds a new task to the specifiedJSONin configuration file。
    """
    print(f"Updating configuration file: {config_file}")
    try:
        # Read existing configuration
        config_data = []
        if os.path.exists(config_file):
            async with aiofiles.open(config_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                # Handling empty files
                if content.strip():
                    try:
                        config_data = json.loads(content)
                        print(f"Successfully read existing configuration, current number of tasks: {len(config_data)}")
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse configuration file, new configuration will be created: {e}")
                        config_data = []
        else:
            print(f"Configuration file does not exist, a new file will be created: {config_file}")

        # Add new tasks
        config_data.append(new_task)

        # Write back configuration file
        async with aiofiles.open(config_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(config_data, ensure_ascii=False, indent=2))
            print(f"Configuration file writing completed")

        print(f"success! new tasks '{new_task.get('task_name')}' has been added to {config_file} and enabled。")
        return True
    except json.JSONDecodeError as e:
        error_msg = f"mistake: Configuration file {config_file} Format error, cannot be parsed: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        return False
    except IOError as e:
        error_msg = f"mistake: Failed to read and write configuration file: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        return False
    except Exception as e:
        error_msg = f"mistake: An unknown error occurred while updating the configuration file: {e}"
        sys.stderr.write(error_msg + "\n")
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return False
