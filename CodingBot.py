import discord
import random
import asyncio
import json
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
user_limit = {}

questions = []

def load_questions():
    global questions
    try:
        with open('questions.json', 'r') as f:
            questions = json.load(f)
    except FileNotFoundError:
        print('Questions file not found.')

scores = {}
# Load scores from JSON file if it exists
def load_scores():
    global scores
    try:
        with open('scores.json', 'r') as f:
            scores = json.load(f)
    except FileNotFoundError:
        print('No scores file found. Starting with empty scores dictionary.')

# Save scores to the JSON file
def save_scores():
    with open('scores.json', 'w') as f:
        json.dump(scores, f)

# Load questions and scores
@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.listening, name='question'))
    print(f"Logged in as {client.user}")
    load_scores()
    load_questions()

# Check if user's answer is correct or not
async def check_answer(selected_answer, correct_answer):
    if selected_answer == correct_answer:
        return True
    else:
        return False

leaderboard_message = None
question_in_progress = False

@client.event
async def on_message(message):
    global question_in_progress
    global leaderboard_message
    global scores
    global user_limit

    async def check_answer(selected_answer, correct_answer):
        if selected_answer == correct_answer:
            return True
        else:
            return False
    if message.author.bot:
        return
    if message.content.lower().startswith('question') or message.content.lower().startswith('qst'):
        realuser = message.author
        if user_limit.get(realuser.id) is None:
            question_in_progress = False
            user_limit[realuser.id] = False
        else:
            question_in_progress = user_limit.get(realuser.id)
            for key, value in user_limit.items():
                print(key, "->", value)


        if question_in_progress:
            # Send embed message if a question is already in progress
            embed = discord.Embed(
                title="Error",
                description="A question is already in progress. Please wait for it to finish before starting a new one.",
                color=discord.Color.dark_red()
            )
            await message.reply(embed=embed, delete_after=3)
            await message.delete(delay=2)   
        else:
            user_limit[realuser.id] = True
            while True:
                # Get random question
                question = random.choice(questions)
                # Shuffle the order of answer choices
                shuffled_answers = random.sample(question['answers'], len(question['answers']))
                # Get the index of the correct answer in the original list of answer choices
                correct_answer_index = question['correct_answer']
                # Create embed with question and choices
                embed = discord.Embed(
                    title="Answer the question",
                    description=f"{question['question']}\n\nA. {shuffled_answers[0]}\n\nB. {shuffled_answers[1]}\n\nC. {shuffled_answers[2]}\n\nD. {shuffled_answers[3]}",
                    color=discord.Color.dark_blue()
                )
                # Send embed message
                question_message = await message.reply(embed=embed)
                # Add reactions to the message
                reactions = ['🇦', '🇧', '🇨', '🇩']
                for reaction in reactions:
                    await question_message.add_reaction(reaction)
                # Wait for user reaction
                def check(reaction, user):
                    return user == message.author and str(reaction.emoji) in reactions
                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=29.0, check=check)
                except asyncio.TimeoutError:
                    shuffled_answers.index(question['answers'][correct_answer_index])
                    embed = discord.Embed(
                        title="Time's up!",
                        description=f"You ran out of time to answer the question.\n\nThe correct answer is {question['answers'][correct_answer_index]}",
                        color=discord.Color.dark_red()
                    )
                    await message.reply(embed=embed)
                    user_limit[realuser.id] = False
                    await question_message.clear_reactions()
                    question_in_progress = False
                    break
                else:
                    # Check if answer is correct
                    selected_answer = reactions.index(str(reaction.emoji))
                    if await check_answer(selected_answer, shuffled_answers.index(question['answers'][correct_answer_index])):
                        user_id = str(user.id)
                        # Add score for the user
                        if user_id in scores:
                            scores[user_id] += 1
                        else:
                            scores[user_id] = 1
                        save_scores()
                        # Create embed with correct answer
                        embed = discord.Embed(
                            title="Correct!",
                            description=question['answers'][correct_answer_index],
                            color=discord.Color.green()
                        )
                        await message.reply(embed=embed)
                        await asyncio.sleep(2)
                    else:
                        # Create embed with incorrect answer and correct answer
                        embed = discord.Embed(
                        title="Incorrect!",
                        description=f"You chose {shuffled_answers[selected_answer]}\n\nThe correct answer is {question['answers'][correct_answer_index]}",
                        color=discord.Color.red()
                        )
                        await message.reply(embed=embed)
                        await asyncio.sleep(2)
                        user_limit[realuser.id] = False
                        await question_message.clear_reactions()
                        break

                    await question_message.clear_reactions()
                    user_limit[realuser.id] = False

    if message.content.lower() in ['leaderboard', 'lb']:
        if not scores:
            # Create new leaderboard message with no scores yet
            leaderboard_embed = discord.Embed(
                title="Leaderboard",
                description="There are no scores yet.",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=leaderboard_embed)
        else:
            # Update existing leaderboard message
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
            leaderboard_embed = discord.Embed(
                title="Leaderboard",
                description="\n".join([f"{i+1}. <@{user}>: {score}" for i, (user, score) in enumerate(sorted_scores)]),
                color=discord.Color.blue()
            )
            leaderboard_message = await message.channel.send(embed=leaderboard_embed)

    if message.content.lower() == 'myscore' or message.content.lower() == 'mscr':
        user_id = str(message.author.id)
        if user_id in scores:
            score = scores[user_id]
            embed = discord.Embed(
                title="Your Score",
                description=f"You have {score} points, keep going!",
                color=discord.Color.purple()
            )
            await message.reply(embed=embed)
        else:
            embed = discord.Embed(
                title="Your Score",
                description="You have no points yet.",
                color=discord.Color.purple()
            )
            await message.reply(embed=embed)

    if message.content.lower() == 'commands':
        commands = discord.Embed(
                    title="CodingBot Commands",
                    description=f"**Here are the available commands that you can use:**\n\n"
                f"```fix\n \n commands - Show the available commands.\n ```"
                f"```fix\n \n leaderboard / lb - Show the top 10 players with the highest \n points.\n ```"
                f"```fix\n \n question / qst - Get asked a random question to programming \n languages that are covered in the ALX program.\n ```"
                f"```fix\n \n myscore / mscr - Show your current points/score.\n ```",
                color=discord.Color.blurple()
                )
        await message.reply(embed=commands)

TOKEN = "TOKEN"  
client.run(TOKEN)
