#!/bin/bash

# Speech Coach PostgreSQL Docker Management Script
# This script helps manage the PostgreSQL Docker container for the Speech Coach application

CONTAINER_NAME="speech_coach"
DB_NAME="speech_coach"
DB_USER="postgres"
DB_PASSWORD="speech_coach_password"
HOST_PORT="5433"
CONTAINER_PORT="5432"
POSTGRES_VERSION="15"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 {start|stop|restart|status|logs|shell|reset|backup|restore}"
    echo ""
    echo "Commands:"
    echo "  start    - Start PostgreSQL container"
    echo "  stop     - Stop PostgreSQL container"
    echo "  restart  - Restart PostgreSQL container"
    echo "  status   - Show container status"
    echo "  logs     - Show container logs"
    echo "  shell    - Open PostgreSQL shell"
    echo "  reset    - Remove and recreate container (WARNING: deletes all data)"
    echo "  backup   - Backup database to file"
    echo "  restore  - Restore database from backup file"
}

start_container() {
    echo -e "${BLUE}Starting PostgreSQL container...${NC}"
    
    # Check if container exists
    if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        # Container exists, start it
        docker start $CONTAINER_NAME
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ PostgreSQL container started successfully${NC}"
            echo -e "${YELLOW}📍 Connection details:${NC}"
            echo "   Host: localhost"
            echo "   Port: $HOST_PORT"
            echo "   Database: $DB_NAME"
            echo "   User: $DB_USER"
        else
            echo -e "${RED}❌ Failed to start container${NC}"
            exit 1
        fi
    else
        # Container doesn't exist, create and start it
        echo -e "${BLUE}Creating new PostgreSQL container...${NC}"
        docker run --name $CONTAINER_NAME \
            -e POSTGRES_DB=$DB_NAME \
            -e POSTGRES_USER=$DB_USER \
            -e POSTGRES_PASSWORD=$DB_PASSWORD \
            -p $HOST_PORT:$CONTAINER_PORT \
            -d postgres:$POSTGRES_VERSION
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ PostgreSQL container created and started${NC}"
            echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
            sleep 5
            echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
            echo -e "${YELLOW}📍 Connection details:${NC}"
            echo "   Host: localhost"
            echo "   Port: $HOST_PORT"
            echo "   Database: $DB_NAME"
            echo "   User: $DB_USER"
        else
            echo -e "${RED}❌ Failed to create container${NC}"
            exit 1
        fi
    fi
}

stop_container() {
    echo -e "${BLUE}Stopping PostgreSQL container...${NC}"
    docker stop $CONTAINER_NAME
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL container stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop container${NC}"
        exit 1
    fi
}

restart_container() {
    echo -e "${BLUE}Restarting PostgreSQL container...${NC}"
    docker restart $CONTAINER_NAME
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PostgreSQL container restarted${NC}"
    else
        echo -e "${RED}❌ Failed to restart container${NC}"
        exit 1
    fi
}

show_status() {
    echo -e "${BLUE}Container status:${NC}"
    docker ps -a --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_logs() {
    echo -e "${BLUE}Container logs:${NC}"
    docker logs $CONTAINER_NAME
}

open_shell() {
    echo -e "${BLUE}Opening PostgreSQL shell...${NC}"
    echo -e "${YELLOW}Type \\q to exit${NC}"
    docker exec -it $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
}

reset_container() {
    echo -e "${RED}⚠️  WARNING: This will delete all database data!${NC}"
    read -p "Are you sure you want to reset the container? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${BLUE}Removing existing container...${NC}"
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
        
        echo -e "${BLUE}Creating new container...${NC}"
        start_container
        echo -e "${GREEN}✅ Container reset completed${NC}"
    else
        echo -e "${YELLOW}Reset cancelled${NC}"
    fi
}

backup_database() {
    BACKUP_FILE="speech_coach_backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${BLUE}Creating database backup...${NC}"
    docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database backed up to: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        exit 1
    fi
}

restore_database() {
    if [ -z "$2" ]; then
        echo -e "${RED}❌ Please provide backup file path${NC}"
        echo "Usage: $0 restore <backup_file.sql>"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Restoring database from: $BACKUP_FILE${NC}"
    docker exec -i $CONTAINER_NAME psql -U $DB_USER $DB_NAME < $BACKUP_FILE
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored successfully${NC}"
    else
        echo -e "${RED}❌ Restore failed${NC}"
        exit 1
    fi
}

# Main script logic
case "$1" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    reset)
        reset_container
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database "$@"
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

exit 0
