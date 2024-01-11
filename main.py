import argparse
import time
import openai
from github import Github


# Function to authenticate and get GitHub repository
def authenticate_github(github_token, repository_url):
    g = Github(github_token)
    repo = g.get_repo(repository_url)
    return repo


# Function to fetch code from a GitHub repository
def fetch_repository_code(repo, path='/'):
    branch = repo.default_branch
    contents = repo.get_contents(path, ref=branch)
    code = []

    for file in contents:
        # Check if it's a file (not a directory)
        if file.type == "file":
            file_content = repo.get_contents(file.path, ref=branch)
            try:
                if file_content.encoding == "base64":
                    decoded_content = file_content.decoded_content.decode('UTF-8')
                    code.append(decoded_content)
            except UnicodeDecodeError as e:
                print(f"Error decoding {file.path}: {e}")
        elif file.type == "dir":
            # Recursive call to fetch files within the directory
            code.extend(fetch_repository_code(repo, file.path))

    return code


# Function to analyze code using ChatGPT
def analyze_code_with_chatgpt(code):
    # Use the OpenAI API to interact with ChatGPT
    openai.api_key = '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'
    # Split the code into chunks
    code_chunks = [code[i] for i in range(0, len(code))]
    analysis_output = ""
    retry_after = 5
    max_retry = 3
    # Analyze each code chunk
    for chunk in code_chunks:
        prompt = f"Code analysis: {chunk}"
        for retry_count in range(max_retry):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You will be provided with a piece of code, and your task is to provide insights and also"
                                       "provide Suggestions for code refactoring and improvements. Identify areas for efficiency increase, such as reducing time"
                                       "complexity. Suggest additional test cases for better coverage. Pinpointing bugs with possible solutions or preventive measures. "
                                       "always give code if there are some suggesstions."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300,
                    top_p=1
                )
                analysis_output += response.choices[0].message.content + '\n'
                break
            except Exception as e:
                print(f"{e}. Waiting for {retry_after} seconds.")
                time.sleep(retry_after)
    return analysis_output


# Function to report findings and suggestions
def generate_report(repository_url, analysis_output):
    report = f"GitHub Repository: {repository_url}\n\n"
    report += f"Code Analysis Output:\n{analysis_output}\n\n"
    return report


def main(github_token, repository_url):
    # Authenticate GitHub
    repo = authenticate_github(github_token, repository_url)
    # Fetch code from the repository
    code = fetch_repository_code(repo)
    # Analyze code using ChatGPT
    analysis_output = analyze_code_with_chatgpt(code)

    report = generate_report(repository_url, analysis_output)
    with open("analysis_report.txt", "w") as file:
        file.write(report)


if __name__ == "__main__":
    github_token = "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"
    parser = argparse.ArgumentParser(description='Fetch code from a GitHub repository.')
    parser.add_argument('repository', help='GitHub repository in the format "owner/repo"')
    args = parser.parse_args()

    # Split the owner and repo from the input
    owner, repo_name = args.repository.split('/')

    main(github_token, repository_url=f"{owner}/{repo_name}")
