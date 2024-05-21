import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import pandas as pd
import numpy as np
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load the traits data from Excel
file_path = "D:/大三下/基因演算法/project_dating/特質編號.xlsx"
traits_df = pd.read_excel(file_path)
traits_dict = dict(zip(traits_df['特質名稱'], traits_df['特質編號']))
inverse_traits_dict = {v: k for k, v in traits_dict.items()}  # To get the Chinese names back from codes

# States for conversation handler
CHOOSING_GENDER, ASKING_NAME, CHOOSING_TRAITS, CHOOSING_IDEAL_TRAITS, CONFIRMING_CHOICES, STORING = range(6)

# Initialize the customer list
customer = []

# Function to start the bot
async def start(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()  # Clear user data at the start of each round
    reply_keyboard = [['女生', '男生']]
    await update.message.reply_text(
        '請選擇您的性別:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_GENDER

# Function to handle gender choice
async def choose_gender(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    gender = update.message.text

    # Count the number of males and females already in the customer list
    male_count = len([c for c in customer if c[1] == '男生'])
    female_count = len([c for c in customer if c[1] == '女生'])

    if gender == '男生' and female_count < 3:
        await update.message.reply_text('Lady first ><')
        return CHOOSING_GENDER
    elif gender == '女生' and female_count >= 3:
        await update.message.reply_text('本輪配對女生名額已滿，下次請早><')
        return CHOOSING_GENDER
    elif gender == '男生' and male_count >= 3:
        await update.message.reply_text('本輪配對男生名額已滿，下次請早><')
        return CHOOSING_GENDER

    context.user_data['gender'] = gender
    if gender == '女生':
        await update.message.reply_text('小姐您好，歡迎您回到戀愛包廂，請問您的大名是？')
    else:
        await update.message.reply_text('先生您好，歡迎您回到戀愛包廂，請問您的大名是？')

    return ASKING_NAME

# Function to handle name input
async def ask_name(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    context.user_data['name'] = name

    reply_keyboard = [[KeyboardButton(trait)] for trait in traits_df['特質名稱'].tolist()]
    await update.message.reply_text(
        '請選擇三個您的特質:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_TRAITS

# Function to handle personal traits choice
async def choose_traits(update: Update, context: CallbackContext) -> int:
    if 'personal_traits' not in context.user_data:
        context.user_data['personal_traits'] = []

    trait = update.message.text
    if trait not in traits_dict:
        await update.message.reply_text('請選擇有效的特質')
        return CHOOSING_TRAITS

    if traits_dict[trait] not in context.user_data['personal_traits']:
        context.user_data['personal_traits'].append(traits_dict[trait])

    if len(context.user_data['personal_traits']) < 3:
        await update.message.reply_text(f'您已選擇的特質: {[inverse_traits_dict[t] for t in context.user_data["personal_traits"]]}\n請再選擇{3 - len(context.user_data["personal_traits"])}個特質')
        return CHOOSING_TRAITS

    reply_keyboard = [[KeyboardButton(trait)] for trait in traits_df['特質名稱'].tolist()]
    await update.message.reply_text(
        '請選擇三個理想型的特質:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_IDEAL_TRAITS

# Function to handle ideal traits choice
async def choose_ideal_traits(update: Update, context: CallbackContext) -> int:
    if 'ideal_traits' not in context.user_data:
        context.user_data['ideal_traits'] = []

    trait = update.message.text
    if trait not in traits_dict:
        await update.message.reply_text('請選擇有效的特質')
        return CHOOSING_IDEAL_TRAITS

    if traits_dict[trait] not in context.user_data['ideal_traits']:
        context.user_data['ideal_traits'].append(traits_dict[trait])

    if len(context.user_data['ideal_traits']) < 3:
        await update.message.reply_text(f'您已選擇的理想型特質: {[inverse_traits_dict[t] for t in context.user_data["ideal_traits"]]}\n請再選擇{3 - len(context.user_data["ideal_traits"])}個理想型特質')
        return CHOOSING_IDEAL_TRAITS

    reply_keyboard = [['沒問題', '我要重選']]
    await update.message.reply_text(
        f"{context.user_data['name']}您好，以下是您的選擇：\n"
        f"您的三個特質：\n"
        f"{inverse_traits_dict[context.user_data['personal_traits'][0]]}，{inverse_traits_dict[context.user_data['personal_traits'][1]]}，{inverse_traits_dict[context.user_data['personal_traits'][2]]}\n"
        f"您理想型的三個特質：\n"
        f"{inverse_traits_dict[context.user_data['ideal_traits'][0]]}，{inverse_traits_dict[context.user_data['ideal_traits'][1]]}，{inverse_traits_dict[context.user_data['ideal_traits'][2]]}\n"
        f"如果這些選擇都正確，請點選'沒問題'，若選擇有誤，請點選'我要重選'",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CONFIRMING_CHOICES

# Function to confirm choices
async def confirm_choices(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    if choice == '我要重選':
        context.user_data.pop('personal_traits', None)
        context.user_data.pop('ideal_traits', None)
        reply_keyboard = [[KeyboardButton(trait)] for trait in traits_df['特質名稱'].tolist()]
        await update.message.reply_text(
            '請選擇三個您的特質:',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CHOOSING_TRAITS
    elif choice == '沒問題':
        await update.message.reply_text("您的選擇太酷啦！稍待片刻，馬上就會顯示您的配對結果！")
        await asyncio.sleep(1)
        return await store_data(update, context)

# Function to store the data and reset conversation
async def store_data(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    user_id = f"cus{len(customer) + 1}"
    user_traits = user_data['personal_traits'] + user_data['ideal_traits']
    customer.append([user_id, user_data['gender'], user_data['name'], user_traits])

    if len(customer) < 6:
        next_user_number = len(customer) + 1
        await update.message.reply_text(f"歡迎第{next_user_number}位使用者")
        await asyncio.sleep(1)
        await start(update, context)
        return CHOOSING_GENDER
    else:
        await update.message.reply_text("新的一輪配對即將展開！大家千萬別走開~")
        await asyncio.sleep(1)
        await run_genetic_algorithm(update)
        return ConversationHandler.END

# Function to run the genetic algorithm and display the result
async def run_genetic_algorithm(update: Update):
    NUM_ITERATION = 1000
    NUM_CHROME = 100
    NUM_BIT = 6
    Pc = 0.85
    Pm = 0.01

    NUM_PARENT = NUM_CHROME
    NUM_CROSSOVER = int(Pc * NUM_CHROME / 2)
    NUM_CROSSOVER_2 = NUM_CROSSOVER * 2
    NUM_MUTATION = int(Pm * NUM_CHROME * NUM_BIT)

    # Example databases (Replace with actual data)
    full_database_men = [
        ["man1", ["ae", "ab", "as", "as", "am", "bd"]],
        ["man2", ["af", "aq", "as", "ad", "ax", "af"]],
        ["man3", ["aa", "cg", "bf", "bf", "aj", "aa"]],
        ["man4", ["cr", "bp", "av", "ag", "ae", "ao"]],
        ["man5", ["am", "az", "au", "ad", "bw", "bb"]],
        ["man6", ["as", "aa", "af", "aa", "bc", "ah"]],
        ["man7", ["as", "bg", "am", "az", "bc", "al"]],
        ["man8", ["bj", "bi", "ap", "ap", "bi", "af"]],
        ["man9", ["bl", "bf", "ai", "bf", "as", "ai"]],
        ["man10", ["af", "bj", "aa", "bk", "ao", "aa"]],
        ["man11", ["ag", "ae", "bj", "aw", "av", "al"]],
        ["man12", ["aq", "ae", "af", "ad", "ao", "cu"]],
        ["man13", ["bb", "ab", "bd", "ak", "cw", "ad"]],
        ["man14", ["ag", "aw", "by", "ae", "am", "au"]],
        ["man15", ["aq", "ae", "af", "ad", "ao", "cu"]],
        ["man16", ["au", "ah", "bv", "aa", "bv", "aj"]],
        ["man17", ["ac", "ae", "bd", "cm", "aa", "ad"]],
        ["man18", ["aq", "ae", "af", "ad", "ao", "cu"]],
        ["man19", ["ax", "ac", "ab", "aj", "ak", "aa"]],
        ["man20", ["ab", "as", "bp", "ab", "an", "ax"]],
        ["man21", ["aq", "ae", "af", "ad", "ao", "cu"]],
        ["man22", ["aa", "aw", "af", "aa", "bo", "bm"]],
        ["man23", ["am", "ah", "aa", "ah", "aa", "ae"]],
        ["man24", ["bd", "al", "ac", "ac", "ak", "ai"]],
        ["man25", ["bq", "ah", "au", "ab", "am", "bv"]],
        ["man26", ["ab", "an", "au", "ak", "an", "au"]],
        ["man27", ["ac", "br", "aq", "ai", "bb", "az"]],
        ["man28", ["aa", "as", "bf", "as", "aa", "af"]],
        ["man29", ["aa", "ax", "ax", "aj", "ao", "bh"]],
        ["man30", ["ct", "bo", "ax", "be", "bj", "av"]],
        ["man31", ["ac", "bh", "bb", "bb", "aq", "ak"]],
        ["man32", ["bp", "bq", "ac", "ac", "cm", "ah"]],
        ["man33", ["ab", "ad", "bh", "cr", "bz", "af"]],
        ["man34", ["aa", "bd", "bb", "ac", "bd", "br"]],
        ["man35", ["af", "as", "ap", "al", "an", "ap"]],
        ["man36", ["ab", "au", "ar", "ai", "am", "cl"]],
        ["man37", ["ai", "af", "bb", "aj", "an", "ac"]],
        ["man38", ["ak", "as", "ay", "ak", "as", "be"]],
        ["man39", ["aa", "ad", "au", "aj", "ab", "ae"]],
        ["man40", ["ab", "bd", "bk", "bc", "by", "az"]],
        ["man41", ["at", "ad", "bz", "bz", "al", "aa"]],
        ["man42", ["ac", "bo", "bp", "aj", "an", "cc"]],
        ["man43", ["ae", "aq", "bk", "ad", "bk", "bo"]],
        ["man44", ["aq", "ae", "af", "ad", "ao", "cu"]],
        ["man45", ["ae", "ab", "av", "bx", "an", "az"]],
        ["man46", ["cb", "bp", "ar", "am", "ag", "an"]],
        ["man47", ["bp", "ab", "be", "al", "al", "an"]],
        ["man48", ["ab", "av", "ac", "ah", "ag", "ac"]],
        ["man49", ["ax", "ah", "cb", "ae", "ax", "ac"]],
        ["man50", ["am", "aw", "au", "bb", "ad", "aq"]],
        ["man51", ["aj", "br", "ay", "cj", "aj", "aq"]],
        ["man52", ["bt", "bb", "bh", "be", "az", "al"]],
        ["man53", ["ae", "bu", "aa", "ae", "aa", "ar"]],
        ["man54", ["ao", "ay", "bw", "an", "aq", "bw"]],
        ["man55", ["ap", "ac", "af", "an", "bl", "aj"]],
        ["man56", ["ah", "ai", "bk", "ar", "ai", "bb"]],
        ["man57", ["aq", "ad", "ap", "ad", "ai", "br"]],
        ["man58", ["ad", "as", "at", "ad", "aq", "at"]],
        ["man59", ["aq", "ap", "bb", "ai", "ak", "aq"]],
        ["man60", ["ad", "am", "ai", "ag", "ad", "ar"]],
        ["man61", ["ax", "au", "ae", "cl", "au", "ad"]],
        ["man62", ["ar", "aq", "bd", "cd", "bb", "ad"]],
        ["man63", ["aq", "ac", "aj", "aa", "an", "ag"]],
        ["man64", ["bi", "ay", "av", "ah", "ag", "bi"]],
        ["man65", ["aa", "af", "bd", "bd", "aa", "bf"]],
        ["man66", ["ae", "ab", "am", "ae", "bg", "ao"]],
        ["man67", ["af", "aw", "ar", "ar", "ap", "ac"]],
        ["man68", ["av", "bi", "ah", "ah", "bt", "an"]],
        ["man69", ["aa", "av", "aa", "aa", "an", "ae"]],
        ["man70", ["aw", "ac", "au", "at", "ad", "bj"]],
        ["man71", ["bi", "aq", "at", "ad", "bk", "aq"]],
        ["man72", ["az", "aq", "ai", "ae", "aq", "bi"]],
        ["man73", ["ab", "ap", "av", "ab", "av", "ap"]],
        ["man74", ["at", "ap", "ab", "aa", "ac", "ak"]],
        ["man75", ["af", "bg", "aa", "ac", "aj", "an"]],
        ["man76", ["aj", "bl", "ar", "bj", "ah", "aj"]],
        ["man77", ["ad", "ah", "ac", "ah", "aa", "ad"]],
        ["man78", ["ap", "ay", "ac", "ae", "ac", "ad"]],
        ["man79", ["bg", "ap", "ad", "ax", "bm", "aa"]],
        ["man80", ["bj", "ch", "bq", "cf", "ap", "bj"]],
        ["man81", ["bu", "ao", "bw", "ao", "an", "cc"]],
        ["man82", ["an", "af", "au", "ac", "al", "at"]],
        ["man83", ["ae", "ay", "aw", "ae", "ag", "aa"]],
        ["man84", ["ae", "ao", "am", "ar", "co", "bf"]],
        ["man85", ["ab", "bu", "ax", "cn", "ao", "an"]],
        ["man86", ["au", "al", "bb", "ak", "ak", "ak"]],
        ["man87", ["br", "bs", "am", "ak", "ah", "ai"]],
        ["man88", ["am", "ap", "ae", "ag", "aj", "ak"]],
        ["man89", ["bt", "al", "cj", "cn", "bt", "ad"]],
        ["man90", ["ag", "ad", "bo", "am", "bo", "ad"]],
        ["man91", ["ag", "bb", "aa", "aa", "ae", "af"]],
        ["man92", ["aq", "ad", "au", "aj", "am", "aq"]],
        ["man93", ["bc", "ab", "av", "bm", "ar", "bf"]],
        ["man94", ["ar", "bd", "ai", "am", "ae", "ac"]],
        ["man95", ["ad", "ae", "ab", "ad", "ac", "bq"]],
        ["man96", ["ai", "ad", "bw", "ai", "au", "bw"]],
        ["man97", ["ac", "bc", "av", "ar", "ak", "az"]],
        ["man98", ["au", "ac", "ay", "aq", "al", "aw"]],
        ["man99", ["au", "bx", "af", "aa", "ag", "au"]],
        ["man100", ["av", "ah", "ab", "aj", "ah", "at"]],
        ["man101", ["av", "as", "ak", "ak", "ah", "ai"]],
        ["man102", ["af", "ah", "bt", "ad", "aq", "ac"]],
        ["man103", ["aa", "cn", "aw", "af", "bx", "af"]],
        ["man104", ["bl", "ao", "ak", "ax", "bp", "ai"]],
        ["man105", ["ay", "as", "bg", "ag", "ad", "as"]],
        ["man106", ["aa", "ab", "bk", "bi", "ae", "as"]],
        ["man107", ["am", "ai", "al", "aw", "cp", "am"]],
        ["man108", ["ar", "af", "aw", "bi", "ar", "br"]],
        ["man109", ["ab", "cl", "ae", "co", "ae", "al"]],
        ["man110", ["ao", "at", "bu", "ad", "ao", "af"]],
        ["man111", ["bc", "bi", "bh", "ag", "ay", "ak"]],
        ["man112", ["ac", "ab", "as", "al", "aj", "an"]],
        ["man113", ["af", "ae", "ah", "ag", "ar", "an"]],
        ["man114", ["ar", "ah", "au", "ag", "au", "aa"]],
        ["man115", ["ac", "ab", "bc", "ac", "ay", "aq"]],
        ["man116", ["ai", "ah", "af", "ae", "am", "al"]],
        ["man117", ["au", "aa", "bg", "ci", "ap", "ac"]],
        ["man118", ["ac", "at", "ad", "aa", "at", "ad"]],
        ["man119", ["ah", "af", "aa", "aa", "bx", "ae"]],
        ["man120", ["bd", "cl", "af", "az", "am", "ak"]],
        ["man121", ["af", "ah", "av", "am", "ah", "at"]],
        ["man122", ["ac", "af", "cf", "cf", "am", "ae"]],
        ["man123", ["aj", "ab", "at", "aa", "ar", "an"]],
        ["man124", ["bk", "as", "af", "bk", "cp", "az"]],
        ["man125", ["af", "ae", "bg", "ae", "ae", "ab"]],
        ["man126", ["ad", "bs", "ae", "ad", "ay", "aj"]],
        ["man127", ["ak", "az", "ae", "an", "ao", "ao"]],
        ["man128", ["aw", "ad", "ac", "bu", "an", "aj"]],
        ["man129", ["af", "ae", "ab", "ae", "aa", "ac"]],
        ["man130", ["av", "cq", "ap", "cq", "ai", "aa"]],
        ["man131", ["ab", "aj", "ah", "ab", "bm", "an"]],
        ["man132", ["ae", "at", "bc", "ag", "by", "af"]],
        ["man133", ["ad", "af", "be", "bt", "ag", "an"]],
        ["man134", ["al", "ck", "bk", "al", "aq", "bk"]],
        ["man135", ["ad", "aw", "ap", "ad", "an", "at"]],
        ["man136", ["ab", "bg", "ad", "be", "ac", "ah"]],
        ["man137", ["af", "aw", "ay", "aa", "an", "bl"]],
        ["man138", ["aw", "as", "av", "aa", "bt", "by"]],
        ["man139", ["aa", "am", "bc", "ak", "aa", "bj"]],
        ["man140", ["bi", "bl", "bf", "bi", "ay", "bk"]],
        ["man141", ["ab", "be", "bk", "ag", "bs", "bx"]],
        ["man142", ["au", "aa", "bc", "aa", "ab", "bo"]],
        ["man143", ["ac", "aw", "af", "ac", "ad", "aq"]],
        ["man144", ["ai", "ab", "al", "ac", "aw", "ai"]],
        ["man145", ["av", "as", "aq", "aw", "bl", "ax"]],
        ["man146", ["at", "bp", "ae", "aa", "ah", "cc"]],
        ["man147", ["as", "aw", "be", "as", "ah", "bk"]],
        ["man148", ["bz", "ab", "ap", "ak", "bb", "bm"]],
        ["man149", ["ah", "av", "au", "ad", "ag", "aq"]],
        ["man150", ["af", "bc", "au", "bc", "al", "aw"]],
        ["man151", ["ab", "aw", "aw", "am", "ad", "ao"]],
        ["man152", ["ah", "ai", "ad", "ah", "ai", "ad"]],
        ["man153", ["bl", "ab", "au", "ax", "ao", "az"]],
        ["man154", ["ap", "af", "ac", "be", "am", "ad"]],
        ["man155", ["ci", "af", "ad", "bf", "bk", "ah"]],
        ["man156", ["aa", "at", "ah", "aa", "bi", "bd"]],
        ["man157", ["ab", "aa", "ay", "aa", "aq", "ak"]],
        ["man158", ["ae", "cf", "ao", "aj", "bd", "ac"]],
        ["man159", ["ab", "ah", "aq", "ar", "bd", "ad"]],
        ["man160", ["am", "ai", "bh", "ag", "ai", "ax"]],
        ["man161", ["bq", "ad", "ab", "am", "bm", "ad"]],
        ["man162", ["ad", "bg", "am", "ao", "al", "ad"]],
        ["man163", ["bg", "bp", "bq", "ao", "ay", "bm"]],
        ["man164", ["ah", "ab", "ac", "an", "bv", "ac"]],
        ["man165", ["aa", "av", "aw", "al", "al", "ac"]],
        ["man166", ["bv", "aa", "cd", "aa", "ac", "ah"]],
        ["man167", ["bq", "cd", "af", "af", "ad", "at"]],
        ["man168", ["bh", "ag", "am", "an", "am", "cc"]],
        ["man169", ["ao", "ap", "an", "an", "aa", "al"]],
        ["man170", ["bx", "ap", "aa", "ag", "aa", "ah"]],
        ["man171", ["ae", "am", "af", "am", "an", "ae"]],
        ["man172", ["bd", "bc", "ae", "ak", "aa", "bd"]],
        ["man173", ["at", "au", "ay", "at", "aa", "ak"]],
        ["man174", ["aa", "ab", "bp", "be", "al", "cc"]],
        ["man175", ["ah", "ad", "ap", "ae", "ap", "ac"]],
        ["man176", ["af", "bg", "bh", "aa", "ak", "af"]],
        ["man177", ["ae", "bp", "cj", "ag", "cj", "ai"]],
        ["man178", ["ay", "ae", "ag", "ay", "bq", "ag"]],
        ["man179", ["ag", "ay", "ae", "ag", "ae", "ay"]],
        ["man180", ["ah", "au", "ch", "ag", "bf", "at"]],
        ["man181", ["bl", "ae", "ai", "ag", "ai", "bl"]],
        ["man182", ["ab", "bo", "ai", "ae", "bg", "ab"]],
        ["man183", ["ad", "bd", "bi", "az", "af", "af"]],
        ["man184", ["bq", "at", "aa", "ag", "aj", "aa"]],
        ["man185", ["ae", "af", "br", "bm", "ai", "az"]],
        ["man186", ["af", "ch", "aa", "aa", "af", "ah"]],
        ["man187", ["ak", "as", "aa", "ak", "as", "aa"]],
        ["man188", ["br", "bh", "az", "ad", "az", "ak"]],
        ["man189", ["ak", "bt", "af", "af", "az", "bb"]],
        ["man190", ["ad", "ac", "ag", "ad", "aj", "am"]],
        ["man191", ["ck", "ae", "ch", "aj", "at", "am"]],
        ["man192", ["af", "bz", "be", "ap", "al", "az"]],
        ["man193", ["bg", "bc", "at", "az", "ae", "al"]],
        ["man194", ["af", "ac", "al", "bm", "ah", "ag"]],
        ["man195", ["bb", "ao", "ad", "ad", "bb", "at"]],
        ["man196", ["ab", "ap", "bt", "ab", "ag", "ap"]],
        ["man197", ["ac", "aa", "ab", "ac", "aa", "bc"]],
        ["man198", ["bj", "af", "ap", "ac", "aj", "ak"]],
        ["man199", ["aq", "cb", "ay", "be", "aj", "at"]],
        ["man200", ["af", "by", "ap", "bs", "bo", "bg"]],
        ["man201", ["bv", "ah", "cd", "aa", "ah", "bv"]],
        ["man202", ["bl", "bc", "cx", "bl", "bc", "cx"]],
        ["man203", ["at", "aj", "av", "by", "aj", "an"]],
        ["man204", ["bd", "ae", "bc", "az", "bd", "ac"]],
        ["man205", ["ac", "ay", "ap", "ap", "ac", "ah"]],
        ["man206", ["bu", "af", "ab", "ab", "ad", "at"]],
        ["man207", ["bh", "am", "ag", "an", "cc", "am"]],
        ["man208", ["ay", "ag", "ah", "aj", "ay", "bz"]],
        ["man209", ["as", "cz", "ah", "as", "bg", "ah"]],
        ["man210", ["aj", "as", "af", "as", "aa", "an"]],
        ["man211", ["ai", "ae", "bl", "ag", "bb", "ar"]],
        ["man212", ["ah", "cs", "af", "am", "ad", "ai"]],
        ["man213", ["af", "ag", "bw", "af", "ar", "ak"]],
        ["man214", ["ay", "ac", "ab", "ar", "ac", "ai"]],
        ["man215", ["ai", "af", "ab", "ag", "ai", "ar"]],
        ["man216", ["ab", "cd", "at", "ad", "ab", "an"]],
        ["man217", ["aw", "ac", "ab", "ad", "al", "ag"]],
        ["man218", ["an", "ah", "bg", "an", "aa", "al"]],
        ["man219", ["af", "al", "aw", "bb", "bm", "au"]],
        ["man220", ["by", "af", "au", "ae", "ao", "bi"]],
        ["man221", ["bj", "aa", "bc", "aa", "ab", "bo"]],
        ["man222", ["be", "ai", "cd", "bm", "ai", "aj"]],
        ["man223", ["cv", "bq", "bp", "ag", "ad", "aj"]],
        ["man224", ["bc", "bu", "ax", "cc", "af", "aw"]],
        ["man225", ["ae", "ab", "ah", "ag", "ar", "an"]],
        ["man226", ["ah", "af", "ab", "ar", "bd", "ab"]],
        ["man227", ["bl", "av", "aa", "at", "ah", "af"]],
        ["man228", ["bc", "ap", "bo", "ag", "ap", "az"]],
        ["man229", ["al", "cd", "at", "ai", "al", "bj"]],
        ["man230", ["ap", "ab", "ae", "ao", "ai", "ax"]],
        ["man231", ["cd", "ac", "ap", "ag", "cd", "at"]]
    ]

    full_database_women = [
        ["woman1", ["cd", "aw", "aa", "bk", "ai", "bf"]],
        ["woman2", ["af", "aw", "am", "ab", "bh", "az"]],
        ["woman3", ["ac", "ar", "bc", "bp", "ac", "av"]],
        ["woman4", ["ct", "av", "cb", "cr", "av", "ab"]],
        ["woman5", ["ar", "cd", "ae", "aa", "bk", "av"]],
        ["woman6", ["ai", "am", "cw", "ai", "am", "cl"]],
        ["woman7", ["bg", "ay", "ad", "ad", "be", "ab"]],
        ["woman8", ["ac", "aq", "ae", "ay", "ae", "by"]],
        ["woman9", ["aj", "ac", "ac", "aj", "ap", "bh"]],
        ["woman10", ["am", "cf", "cf", "aj", "ap", "cb"]],
        ["woman11", ["ag", "cg", "bs", "ad", "aj", "bk"]],
        ["woman12", ["am", "ak", "as", "af", "av", "bh"]],
        ["woman13", ["ag", "ao", "ap", "ab", "bc", "az"]],
        ["woman14", ["ac", "br", "bd", "ai", "bh", "ae"]],
        ["woman15", ["ck", "am", "ad", "ad", "ao", "av"]],
        ["woman16", ["aa", "ag", "ab", "ao", "aa", "ab"]],
        ["woman17", ["ae", "ag", "bl", "cb", "bk", "ay"]],
        ["woman18", ["aa", "co", "al", "ab", "ac", "co"]],
        ["woman19", ["af", "bl", "aj", "aa", "ad", "aq"]],
        ["woman20", ["al", "ao", "ax", "bg", "ao", "bj"]],
        ["woman21", ["ag", "ac", "aj", "aj", "ax", "be"]],
        ["woman22", ["ad", "ag", "al", "av", "ak", "be"]],
        ["woman23", ["am", "ae", "ar", "ab", "ak", "az"]],
        ["woman24", ["aj", "ac", "al", "bh", "bi", "bd"]],
        ["woman25", ["aw", "ar", "bq", "aa", "ab", "ad"]],
        ["woman26", ["bt", "ar", "af", "aj", "cy", "al"]],
        ["woman27", ["aj", "cg", "ay", "aj", "ab", "ac"]],
        ["woman28", ["aq", "bc", "cp", "ab", "ap", "ai"]],
        ["woman29", ["bs", "ae", "ad", "ai", "ae", "aq"]],
        ["woman30", ["ac", "ag", "aq", "ab", "be", "bo"]],
        ["woman31", ["aq", "aj", "al", "al", "ak", "ad"]],
        ["woman32", ["ax", "cd", "av", "bf", "ab", "al"]],
        ["woman33", ["ak", "bb", "ag", "ak", "ai", "ac"]],
        ["woman34", ["ag", "ao", "aa", "ab", "aa", "bj"]],
        ["woman35", ["ag", "am", "ab", "bt", "ag", "ab"]],
        ["woman36", ["aj", "ap", "aq", "ap", "aj", "ab"]],
        ["woman37", ["aq", "al", "ax", "be", "ak", "ax"]],
        ["woman38", ["ac", "ag", "aa", "ax", "bh", "ak"]],
        ["woman39", ["ad", "ar", "av", "bk", "ap", "az"]],
        ["woman40", ["ar", "ah", "al", "am", "ao", "bh"]],
        ["woman41", ["cb", "aq", "ak", "bh", "ak", "bc"]],
        ["woman42", ["bw", "ax", "as", "ai", "az", "bh"]],
        ["woman43", ["aw", "cu", "au", "al", "am", "aq"]],
        ["woman44", ["ab", "ao", "ac", "ab", "ac", "aa"]],
        ["woman45", ["ay", "at", "cj", "ae", "ac", "ak"]],
        ["woman46", ["bt", "bu", "ar", "ab", "av", "ck"]],
        ["woman47", ["bq", "aa", "ae", "ai", "be", "aa"]],
        ["woman48", ["ac", "bd", "aa", "aj", "ad", "az"]],
        ["woman49", ["ae", "aw", "al", "ab", "br", "bj"]],
        ["woman50", ["ay", "ac", "ad", "ai", "am", "ac"]],
        ["woman51", ["bi", "ay", "cs", "as", "ao", "aq"]],
        ["woman52", ["ck", "bw", "an", "cb", "ao", "ax"]],
        ["woman53", ["bb", "ao", "ar", "aq", "ax", "br"]],
        ["woman54", ["as", "aq", "ab", "ab", "as", "ao"]],
        ["woman55", ["cq", "ac", "au", "ac", "ai", "bb"]],
        ["woman56", ["af", "ab", "bg", "aa", "ab", "bo"]],
        ["woman57", ["av", "bh", "cs", "bh", "am", "az"]],
        ["woman58", ["bq", "ab", "al", "ax", "ai", "al"]],
        ["woman59", ["cg", "aa", "bs", "aa", "al", "ao"]],
        ["woman60", ["at", "cn", "ad", "ac", "ad", "ax"]],
        ["woman61", ["an", "aa", "be", "ao", "ah", "ak"]],
        ["woman62", ["cg", "bv", "br", "ak", "bo", "ao"]],
        ["woman63", ["ci", "at", "aj", "cm", "al", "aj"]],
        ["woman64", ["ar", "bs", "ao", "bc", "cg", "ab"]],
        ["woman65", ["ao", "an", "ar", "ab", "aa", "ai"]],
        ["woman66", ["cd", "bj", "ae", "ae", "br", "cy"]],
        ["woman67", ["bs", "am", "al", "bg", "ai", "al"]],
        ["woman68", ["bi", "ac", "ao", "ap", "bp", "an"]],
        ["woman69", ["ao", "bi", "be", "aa", "ar", "ap"]],
        ["woman70", ["an", "ag", "aa", "ag", "bj", "ai"]],
        ["woman71", ["ak", "be", "at", "ak", "af", "bh"]],
        ["woman72", ["bb", "ao", "aa", "ax", "ai", "be"]],
        ["woman73", ["ac", "bd", "ad", "aj", "ab", "ax"]],
        ["woman74", ["ao", "ak", "an", "ab", "aa", "ak"]],
        ["woman75", ["ak", "aj", "aa", "ak", "ae", "ax"]],
        ["woman76", ["au", "ar", "aj", "ai", "ab", "bb"]],
        ["woman77", ["an", "ae", "bj", "ay", "bk", "ak"]],
        ["woman78", ["ag", "ar", "at", "ab", "ac", "ap"]],
        ["woman79", ["ag", "ao", "ac", "ab", "au", "ac"]],
        ["woman80", ["ag", "cd", "af", "bz", "ab", "ai"]],
        ["woman81", ["ag", "al", "as", "ao", "bz", "al"]],
        ["woman82", ["bi", "ax", "bg", "bg", "bb", "ai"]],
        ["woman83", ["cv", "bg", "an", "ac", "aj", "ad"]],
        ["woman84", ["bs", "am", "al", "bg", "ai", "al"]],
        ["woman85", ["bi", "ac", "ap", "bd", "ay", "al"]],
    ]

    def initPop(full_database_men, full_database_women):
        population = []
        for _ in range(NUM_CHROME):
            selected_indices = set()  # To keep track of selected indices
            selected_people = []

            # Randomly select three men
            for _ in range(3):
                while True:
                    index = random.randint(0, len(full_database_men) - 1)
                    if index not in selected_indices:
                        selected_people.append(index)  # Append index
                        selected_indices.add(index)
                        break

            # Randomly select three women
            for _ in range(3):
                while True:
                    index = random.randint(0, len(full_database_women) - 1)
                    if index not in selected_indices:
                        selected_people.append(
                            index + len(full_database_men)
                        )  # Append index and offset by len of men database
                        selected_indices.add(index)
                        break

            population.append(selected_people)

        return population

    def fitness_function(chromosome):
        score = 0
        for j in range(NUM_BIT):
            if j < NUM_BIT / 2:
                # Compare with full_database_men
                pick = chromosome[j]
                for i in range(3):
                    for k in range(3):
                        # If pick's traits match customer's desired traits
                        if full_database_men[pick][1][i] == customer[j][3][3 + k]:
                            score += (3 - k) + (3 - i)
                        if customer[j][3][i] == full_database_men[pick][1][3 + k]:
                            score += (3 - k) + (3 - i)
            else:
                # Compare with full_database_women
                pick = chromosome[j] - len(full_database_men)
                for i in range(3):
                    for k in range(3):
                        if full_database_women[pick][1][i] == customer[j][3][3 + k]:
                            score += (3 - k) + (3 - i)
                        if customer[j][3][i] == full_database_women[pick][1][3 + k]:
                            score += (3 - k) + (3 - i)
        return score

    def evaluatePop(p):  # Evaluate population fitness
        return [fitness_function(p[i]) for i in range(len(p))]

    def selection(p, p_fit):  # Binary tournament selection
        a = []
        for i in range(NUM_PARENT):
            j, k = np.random.choice(NUM_CHROME, 2, replace=False)
            if p_fit[j] > p_fit[k]:
                a.append(p[j])
            else:
                a.append(p[k])
        return a

    def crossover(p):  # Single point crossover
        a = []
        for i in range(NUM_CROSSOVER):
            j, k = np.random.choice(NUM_PARENT, 2, replace=False)
            c = 3
            a.append(p[j][:c] + p[k][c:])
            a.append(p[k][:c] + p[j][c:])
        return a

    def mutation(p):  # Mutation
        for _ in range(NUM_MUTATION):
            chrom = np.random.randint(len(p))
            gene = np.random.randint(NUM_BIT)
            if gene < NUM_BIT / 2:
                r = np.random.randint(len(full_database_men))
                p[chrom][gene] = r
            else:
                r = np.random.randint(len(full_database_women)) + len(full_database_men)
                p[chrom][gene] = r

    def sortChrome(a, a_fit):  # Sort chromosomes by fitness
        a_index = list(range(len(a)))
        a_fit, a_index = zip(*sorted(zip(a_fit, a_index), reverse=True))
        return [a[i] for i in a_index], list(a_fit)

    def replace(p, p_fit, a, a_fit):  # Survival of the fittest
        b = p + a
        b_fit = p_fit + a_fit
        b, b_fit = sortChrome(b, b_fit)
        return b[:NUM_CHROME], b_fit[:NUM_CHROME]

    # Main program
    pop = initPop(full_database_men, full_database_women)  # Initialize population
    pop_fit = evaluatePop(pop)  # Evaluate initial population fitness

    best_outputs = [np.max(pop_fit)]  # Record best fitness value
    mean_outputs = [np.mean(pop_fit)]  # Record mean fitness value

    for i in range(NUM_ITERATION):
        parent = selection(pop, pop_fit)  # Select parents
        offspring = crossover(parent)  # Crossover
        mutation(offspring)  # Mutation
        offspring_fit = evaluatePop(offspring)  # Evaluate offspring fitness
        pop, pop_fit = replace(
            pop, pop_fit, offspring, offspring_fit
        )  # Replace old population

        best_outputs.append(np.max(pop_fit))  # Record best fitness value
        mean_outputs.append(np.mean(pop_fit))  # Record mean fitness value

    # Display detailed output for the best chromosome
    best_chromosome = pop[0]
    detailed_output = [
        (
            idx
        )
        for idx in best_chromosome
    ]

    result_text = "最佳配對結果：\n"
    for idx, match in enumerate(detailed_output):
        user_name = customer[idx][2]
        match_index = match if idx < 3 else match - len(full_database_men)
        match_traits = (
            full_database_men[match][1] if idx < 3 else full_database_women[match_index][1]
        )
        match_traits_chinese = [inverse_traits_dict[trait] for trait in match_traits[:3]]
        gender = "man" if idx < 3 else "woman"
        result_text += f"{idx + 1}. {user_name} 配對到 {gender}{match + 1}，他的特質有[{', '.join(match_traits_chinese)}]\n"

    result_text += f"本次配對結果的分數：{best_outputs[-1]}"

    await update.message.reply_text(result_text)

# Main function to set up the bot
def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7111678220:AAE1uj-cMDvrxMjQqb9lGLJNrH3c9ldW3e8").build()

    # Add conversation handler with the states CHOOSING_GENDER, ASKING_NAME, CHOOSING_TRAITS, CHOOSING_IDEAL_TRAITS, CONFIRMING_CHOICES, STORING
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_gender)],
            ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            CHOOSING_TRAITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_traits)],
            CHOOSING_IDEAL_TRAITS: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_ideal_traits)],
            CONFIRMING_CHOICES: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_choices)],
            STORING: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_data)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
