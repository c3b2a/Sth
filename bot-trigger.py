import sys, time, json, telepot
from uuid import uuid4
from time import sleep
from os.path import exists
from telepot.loop import MessageLoop
from threading import Thread

fname = "interval_data.json"
owner = 0
bot_token = ""
default_lim = 30

if len(sys.argv) == 3:
    owner = int(sys.argv[2])
    bot_token = sys.argv[1]
else:
    print("Args Error")
    exit(1)

print(f"bot_token: {bot_token}")

data = {"user": {}, "data": {}, "time": {}, "mlim": {}}
if exists(fname):
    with open(fname, "r") as f:
        data = json.loads(f.read())
else:
    with open(fname, "w") as f:
        f.write(json.dumps(data))

print(f"msg_data: {str(data)}")

bot = telepot.Bot(bot_token)
print(bot.getMe())

def random_str():
    return str(uuid4()).replace('-', '')

def is_num(x: str):
    try:
        x = int(x)
        return isinstance(x, int)
    except ValueError:
        return False

def is_time(x: str):
    l = x.split(":")
    if len(l) != 3: return False
    if not is_num(l[0]) or not 0 <= int(l[0]) < 24: return False
    if not is_num(l[1]) or not 0 <= int(l[1]) < 60: return False
    if not is_num(l[2]) or not 0 <= int(l[2]) < 60: return False
    return True

def calc_time(x: list):
    return int(x[2]) + int(x[1]) * 60 + int(x[0]) * 3600

def get_lim(x: str):
    if x in data["mlim"]: return int(data["mlim"][x])
    else: return default_lim

def handle(context):
    answered = False
    content_type, chat_type, chat_id = telepot.glance(context)
    if content_type == "text":
        texts = context["text"].split("\n")
        for text in texts:
            text = text.replace(r"\n", "\n")
            parse = []
            for s in text.split(" "):
                if len(s.split()) != 0:
                    parse.append(s)
            if parse[0] == "/new" and len(parse) >= 4 and is_time(parse[1]) and is_num(parse[2]):
                if len(data["user"].get(str(chat_id), [])) >= get_lim(str(chat_id)):
                    bot.sendMessage(chat_id, f"您的消息数量限制是 {get_lim(str(chat_id))} 个")
                    answered = True
                    return
                send_msg = " ".join(parse[3:])
                send_time = list(map(int, parse[1].split(":")))
                time_key = calc_time(send_time)
                data_key = random_str()
                p_user = data["user"].get(str(chat_id), [])
                p_user.append(data_key)
                p_time = data["time"].get(str(time_key), [])
                p_time.append(data_key)
                data["data"][str(data_key)] = f"{parse[1]}|{chat_id}|{str(int(parse[2]))}|{send_msg}"
                data["user"][str(chat_id)] = p_user
                data["time"][str(time_key)] = p_time
                with open(fname, "w") as f:
                    f.write(json.dumps(data))
                bot.sendMessage(chat_id, "添加成功")
                answered = True
            elif parse[0] == "/del" and len(parse) >= 2:
                msg_1 = []
                msg_2 = []
                for i in range(1, len(parse)):
                    if parse[i] in data["data"]:
                        p_data = data["data"][parse[i]].split("|")
                        if chat_id == int(p_data[1]):
                            time_key = calc_time(p_data[0].split(":"))
                            p_user = data["user"].get(str(chat_id), [])
                            p_time = data["time"].get(str(time_key), [])
                            if parse[i] in p_user and parse[i] in p_time:
                                p_user.remove(parse[i])
                                p_time.remove(parse[i])
                                del data["data"][parse[i]]
                                if len(p_user) == 0: del data["user"][str(chat_id)]
                                else: data["user"][str(chat_id)] = p_user
                                if len(p_time) == 0: del data["time"][str(time_key)]
                                else: data["time"][str(time_key)] = p_time
                                with open(fname, "w") as f:
                                    f.write(json.dumps(data))
                                msg_1.append(parse[i])
                            else:
                                msg_2.append(parse[i])
                        else:
                            msg_2.append(parse[i])
                    else:
                        msg_2.append(parse[i])
                msg_s = ""
                if len(msg_1) > 0: msg_s += "删除成功: " + ", ".join([f"`{p}`" for p in msg_1]) + "\n"
                if len(msg_2) > 0: msg_s += "删除失败: " + ", ".join([f"`{p}`" for p in msg_2]) + "\n"
                bot.sendMessage(chat_id, msg_s)
                answered = True
            elif parse[0] == "/list":
                id_list = data["user"].get(str(chat_id), [])
                if len(id_list) == 0:
                    bot.sendMessage(chat_id, "无定时消息")
                    answered = True
                else:
                    msg_list = ""
                    for msg_id in id_list:
                        msg_get = data["data"].get(msg_id, None)
                        if msg_get:
                            msg_get = msg_get.split("|")
                            send_time = msg_get[0].split(":")
                            for i in range(3):
                                if len(send_time[i]) == 1:
                                    send_time[i] = "0" + send_time[i]
                            send_time = ":".join(send_time)
                            msg_list += f"id: `{msg_id}`\n时间: `{send_time}`\n用户: `{msg_get[2]}`\n信息: `{msg_get[3]}`\n\n"
                    bot.sendMessage(chat_id, msg_list, parse_mode="markdown")
                    answered = True
            elif parse[0] == "/clim" and len(parse) == 3 and is_num(parse[1]):
                if chat_id == owner:
                    if is_num(parse[2]):
                        data["mlim"][str(parse[1])] = parse[2]
                        bot.sendMessage(chat_id, f"已更改 {parse[1]} 的限制为 {parse[2]}")
                        answered = True
                    elif parse[2] == "clear":
                        del data["mlim"][str(parse[1])]
                        bot.sendMessage(chat_id, f"已恢复 {parse[1]} 的限制为默认值 {default_lim}")
                        answered = True
                    else:
                        bot.sendMessage(chat_id, "参数错误")
                        answered = True
                    with open(fname, "w") as f:
                        f.write(json.dumps(data))
                else:
                    bot.sendMessage(chat_id, "无权操作")
                    answered = True
            elif parse[0] != "receive":
                bot.sendMessage(chat_id, "参数错误")
                answered = True
            if not answered:
                bot.sendMessage(chat_id, "未知错误")

MessageLoop(bot, handle).run_as_thread()

def send_msg(chat_id, msg):
    bot.sendMessage(chat_id, msg)

l_time = int(time.time())

while True:
    if int(time.time()) != l_time:
        l_time = int(time.time())
        n_time = time.strftime("%H:%M:%S", time.localtime())
        n_time = str(calc_time(list(map(int, n_time.split(":")))))
        msg_get = data["time"].get(n_time, [])
        for d in msg_get:
            details = data["data"].get(d, None)
            if details:
                details = details.split("|")
                t = Thread(target=send_msg, args=(int(details[1]), f"send_msg|{details[2]}|{details[3]}"))
                t.start()
    sleep(0.01)