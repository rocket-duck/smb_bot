# Запуск бота
docker compose up --build

docker system df

docker system prune -a --volumes -f

docker builder prune --all -f

## Команды бота
/add_chat - добавляет чат, в котором вызвана команда, в список для рассылок. Необходимо использовать только в чатах

/announce - отправляет сообщение, введенное после команды, во все добавленные чаты. Использовать в ЛС бота

/start - запускает бота

/help - отправляет справку по боту

/docs - вызывает меню со ссылками