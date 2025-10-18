# RentingApart - Telegram Bot with Web Scraping

A Telegram bot for apartment rental management with web scraping capabilities and PostgreSQL database.

## Features

- Telegram bot for apartment management
- Web scraping from OLX
- PostgreSQL database for data storage
- Docker containerization
- Web interface for management

## Prerequisites

- Docker and Docker Compose installed
- Telegram Bot Token
- OpenAI API Key (optional, for address extraction)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RentingApart
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**
   Edit `.env` file with your actual values:
   ```env
   TOKEN=your_telegram_bot_token_here
   ADMIN_CHAT_ID=your_admin_chat_id_here
   OPENAI_API_KEY=your_openai_api_key_here
   DB_PASSWORD=your_secure_password_here
   WEB_TOKEN=your_web_token_here
   CLICK_TOKEN=your_click_token_here
   ```

4. **Start the services**
   ```bash
   docker-compose up -d
   ```

5. **Check logs**
   ```bash
   # View all logs
   docker-compose logs -f
   
   # View specific service logs
   docker-compose logs -f bot
   docker-compose logs -f postgres
   docker-compose logs -f web
   ```

## Services

### PostgreSQL Database
- **Port**: 5432
- **Database**: renting_apart_db
- **User**: postgres
- **Password**: Set in `.env` file

### Telegram Bot
- Runs the main bot application
- Connects to PostgreSQL database
- Handles apartment management commands

### Web Interface
- **Port**: 8000
- Web interface for apartment management
- Accessible at `http://localhost:8000`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TOKEN` | Telegram Bot Token | Yes |
| `ADMIN_CHAT_ID` | Admin Chat ID for notifications | Yes |
| `OPENAI_API_KEY` | OpenAI API Key for address extraction | No |
| `DB_NAME` | Database name | No (default: renting_apart_db) |
| `DB_USER` | Database user | No (default: postgres) |
| `DB_PASSWORD` | Database password | Yes |
| `DB_HOST` | Database host | No (default: postgres) |
| `DB_PORT` | Database port | No (default: 5432) |
| `WEB_TOKEN` | Web interface token | No |
| `CLICK_TOKEN` | Payment token | No |

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart bot

# View service status
docker-compose ps

# Execute commands in running container
docker-compose exec bot python -c "print('Hello from bot container')"

# View logs
docker-compose logs -f bot

# Rebuild and start
docker-compose up --build -d
```

## Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d renting_apart_db

# Backup database
docker-compose exec postgres pg_dump -U postgres renting_apart_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres renting_apart_db < backup.sql
```

## Development

For development, you can run services individually:

```bash
# Start only database
docker-compose up postgres -d

# Run bot locally (make sure database is running)
python main.py

# Run web interface locally
python web/app.py
```

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if `TOKEN` is correctly set in `.env`
   - Verify bot token is valid
   - Check bot logs: `docker-compose logs bot`

2. **Database connection issues**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check database logs: `docker-compose logs postgres`
   - Verify database credentials in `.env`

3. **Port conflicts**
   - Change ports in `docker-compose.yml` if 5432 or 8000 are already in use

4. **Permission issues**
   - Ensure Docker has proper permissions
   - Check file permissions for `webscrape/images` directory

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs bot
docker-compose logs postgres
docker-compose logs web

# Check container status
docker-compose ps

# Check resource usage
docker stats
```

## Security Notes

- Never commit `.env` files to version control
- Use strong passwords for database
- Keep API keys secure
- Regularly update dependencies
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

[Add your license information here]