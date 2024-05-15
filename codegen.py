import openai
import re
from github import Github
import os
from dotenv import load_dotenv
import autogen
import requests
import json
import io
import sys

class CodeGen:
    def __init__(self):
        load_dotenv()

        self.open_ai_key = os.getenv("OPEN_AI_KEY")
        self.git_token = os.getenv("GITHUB_KEY")

        self.base_urls = None  # You can specify API base URLs if needed.
        self.api_type = "openai"
        self.api_version = None

    def get_repos(self):
        github_repo = Github(self.git_token)
        git_user = github_repo.get_user()
        return git_user.get_repos()

    def prompt_gpt(self, prompt=""):
        openai.api_key = self.open_ai_key
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    @staticmethod
    def extract_mermaid_script(gpt_response):
        # Regex pattern to find content within ```mermaid ... ```
        pattern = r"```mermaid([\s\S]*?)```"
        match = re.search(pattern, gpt_response)
        if match:
            return match.group(1).strip()  # Returns only the script part
        else:
            return "none"  # If no script is found

    @staticmethod
    def extract_readme(user_repos):
        aRepo = user_repos[10]  # Example: fetching the 11th repo
        readme = aRepo.get_readme()
        return readme.decoded_content.decode('utf-8') if readme else None

    def save_script_to_cloud(self, mermaid_script="", log_monitor="", log_datetime="", reference_id=""):
        url = "https://marxvimrasprod.herokuapp.com/marxvim/stockBot/1.0.0/temp/log/codegen/script"
        headers = {'Content-Type': 'application/json'}
        data = {
            # "logId": log_id,
            "logPlan": mermaid_script,
            "logMonitor": log_monitor,
            "logDatetime": log_datetime,
            "referenceId": reference_id
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response

    def select_teammate(self, user_prompt, teammates):
        # Create a list to store the suitability scores for each teammate
        suitability_scores = []

        # Iterate through each teammate
        for teammate in teammates:
            # Construct a message for OpenAI using the user_prompt and teammate's system_message
            message = f"User prompt: {user_prompt}\nTeam member: {teammate['name']}\nSystem message: {teammate['system_message']}"

            # Use OpenAI to evaluate the message and determine suitability
            response = self.prompt_gpt(message)

            print(response)

            # # Extract the suitability score from the OpenAI response
            # response_text = response.choices[0].text.strip()

            # # Append the teammate's name and suitability score to the list
            # suitability_scores.append((teammate['name'], suitability_score))

        # # Sort the teammates based on suitability scores in descending order
        # sorted_teammates = sorted(suitability_scores, key=lambda x: x[1], reverse=True)

        # # Return the most suitable teammate (the one with the highest score)
        # most_suitable_teammate = sorted_teammates[0]
        most_suitable_teammate = teammates
        return most_suitable_teammate

    def run(self, user_prompt = ""):
        mermaid_script_prompt = (
            "Using Mermaid diagram syntax, create a script for the following task: "
            + user_prompt
            + ". Please provide only the Mermaid script without any additional explanation, comments, or words. If a script cannot be generated for this task, simply return 'none'."
        )

        generated_mermaid_script = self.prompt_gpt(mermaid_script_prompt)
        mermaid_script = self.extract_mermaid_script(generated_mermaid_script)
        self.save_script_to_cloud(mermaid_script=mermaid_script)

        user_repos = self.get_repos()
        readme = self.extract_readme(user_repos)

        print(mermaid_script)

        config_list = [
            {
                'model': 'gpt-4',
                'api_key': self.open_ai_key,
            }
        ]

        config_list_gpt4 = autogen.config_list_from_json(
            "OAI_CONFIG_LIST",
            filter_dict={
                "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
            },
        )

        # Initialize GroupChat and Manager
        llm_config = {"config_list": config_list, "cache_seed": 42}

        teammates = [
            {
                "name": "User_proxy",
                "system_message": "A human admin.",
                "llm_config": llm_config  # Assuming llm_config is defined elsewhere
            },
            {
                "name": "Coder",
                "system_message": "N/A",
                "llm_config": llm_config
            },
            {
                "name": "Product_manager",
                "system_message": "Creative in software product ideas.",
                "llm_config": llm_config
            },
            {
                "name": "Quality_assurance_tester",
                "system_message": "primarily focused on verifying that the software meets the specified quality standards, adheres to coding standards, and is free from defects or bugs",
                "llm_config": llm_config
            }
        ]

        user_proxy = autogen.UserProxyAgent(
            name="User_proxy",
            system_message="A human admin.",
            code_execution_config={"last_n_messages": 2, "work_dir": "groupchat"},
            human_input_mode="NEVER"
        )
        coder = autogen.AssistantAgent(
            name="Coder",
            llm_config=llm_config,
        )
        pm = autogen.AssistantAgent(
            name="Product_manager",
            system_message="Creative in software product ideas.",
            llm_config=llm_config,
        )

        qat = autogen.AssistantAgent(
            name="Quality_assurance_tester",
            system_message="primarily focused on verifying that the software meets the specified quality standards, adheres to coding standards, and is free from defects or bugs",
            llm_config=llm_config,
        )
        print('Beta node batch: [user_proxy, coder, qat, uat, pm, scrum_master]')
        print('Alpha node decision 1: ')
        print(beta_nodes)
        print('Alpha node decision 2: [user_proxy, coder, qat]')
        beta_nodes = self.select_teammate(user_prompt, teammates)
        print('Alpha node decision 1: '+ beta_nodes)
        
        groupchat = autogen.GroupChat(agents=[user_proxy, coder, qat], messages=[], max_round=12)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

        user_proxy.initiate_chat(manager, message=user_prompt)

        buffer = io.StringIO()

        # Save the current stdout so that we can restore it later
        current_stdout = sys.stdout

        # Redirect stdout to the buffer
        sys.stdout = buffer


        # Restore the original stdout
        sys.stdout = current_stdout

        # Get the content of the buffer
        output = buffer.getvalue()

        # Don't forget to close the buffer
        buffer.close()

        # Now output is stored in the 'output' variable
        self.save_script_to_cloud(log_monitor=output)


# %%



# %% [markdown]
# 


