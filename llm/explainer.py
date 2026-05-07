import ollama
import os


def explain_recommendation(board_champions, top_comps):
    """
    board_champions: list of champions the player currently has 
    top_comps: list of recommended comps with win rate info
    """

    prompt = f"""
    You are a Teamfight Tactics (TFT) expert coach.
    A player currently has these champions on their board: {', '.join(board_champions)}.

    Based on match data, the top recommended team compositions to pivot into are:
    {top_comps}

    Give a short, clear explanation (3-5 sentences) of:
    - Which comp to prioritize and why
    - What key champions or traits to look for
    - Any carousel or augment tips

    Be direct and practical. bullet points, just natural language.
    """

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]


if __name__ == "__main__":
    board = ["Jinx", "Jhin", "Caitlyn", "Graves"]
    comps = "1. DarkStar (62% win rate), 2. Astronaut (58% win rate)"

    explanation = explain_recommendation(board, comps)
    print(explanation)