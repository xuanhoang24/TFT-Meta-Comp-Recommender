import ollama


def explain_recommendation(board_champions, top_comps):
    """
    board_champions: list of champions the player currently has
    top_comps: string or list of recommended comps with top4 rate / avg placement info
    """

    board_text = ", ".join(board_champions) if board_champions else "No champions selected"

    prompt = f"""
        You are a Teamfight Tactics (TFT) expert coach.

        The player currently has these champions on their board:
        {board_text}

        Based on match data, the top recommended team compositions are:
        {top_comps}

        Write a short and practical explanation for the player.

        Requirements:
        - Recommend which comp to prioritize and why.
        - Mention what key champions or traits to look for next.
        - Mention item or carousel priorities if relevant.
        - Only use the information provided. Do not invent exact stats, augments, or patch details.
        - Keep it short, around 3-5 sentences.
        - Use clear bullet points.
        """

    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[
                {"role": "user", "content": prompt}
            ],
            options={
                "temperature": 0.3
            }
        )

        return response["message"]["content"]

    except Exception as e:
        return f"AI explanation is unavailable right now. Error: {e}"


if __name__ == "__main__":
    sample_board = ["Jinx", "Jhin", "Caitlyn", "Graves"]
    sample_comps = "1. DarkStar (62% top4 rate), 2. Astronaut (58% top4 rate)"

    explanation = explain_recommendation(sample_board, sample_comps)
    print(explanation)