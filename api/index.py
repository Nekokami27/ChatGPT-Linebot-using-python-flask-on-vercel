line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFAULT_TALKING", default="true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()
event_queue = queue.Queue()

@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 将事件数据放入队列
    event_queue.put(event)

def process_event():
    while True:
        if not event_queue.empty():
            event = event_queue.get()
            # 以下是处理事件的逻辑
            if event.message.type == "text":
                if event.message.text.lower().startswith("hi"):
                    chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
                    reply_msg = chatgpt.get_response().replace("AI:", "", 1)
                    chatgpt.add_msg(f"AI:{reply_msg}\n")
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=reply_msg))
            event_queue.task_done()

# 启动一个后台线程来处理事件
threading.Thread(target=process_event, daemon=True).start()

if __name__ == "__main__":
    app.run()
