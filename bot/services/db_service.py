import aiosqlite
import os
import logging
import csv
from locales.localization import localization
from io import StringIO
from run import db_name, admins_bot, organization_name

class Database:
    def __init__(self, db_connection: str = db_name):
        self.db_connection = db_connection
        self.connection = None

    # region Preparation database

    async def check_database_on_startup(self):
        if not os.path.exists(db_name):
            logging.error (
                f'Critical error, database: {db_name} not found! Trying to create an empty database...'
            )
        else:
            logging.info (
                f'Database found! Path to database: {db_name}'
            )
        try:
            self.connection = await aiosqlite.connect(self.db_connection)
            await self.connection.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            await self.connection.commit()
            logging.info (
                f'The database is correct. Сontinue regular work. Database path: {db_name}'
            )
        except aiosqlite.Error as e:
            logging.critical (
                f'Database in error: \n{e}\n' \
                f'Terminating application. Check database file. This is probably not a valid file: {db_name}'
            )
            self.connection.close()
            os._exit(1)

    async def initialize_content_database(self):
        await self.connection.execute ('PRAGMA foreign_keys = ON')
        self.connection.row_factory = aiosqlite.Row
        logging.info(f'Filling the database with default values!')

        await self.connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_user_id INTEGER PRIMARY KEY,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        )
        await self.connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    organization_id INTEGER DEFAULT 1 REFERENCES organizations(organization_id),
                    event_is_active BOOLEAN DEFAULT TRUE
                )
            '''
        )
        await self.connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS registrations (
                    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    telegram_user_id INTEGER NOT NULL,
                    nickname TEXT,
                    telegram_username TEXT,
                    additional_information TEXT,
                    reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    
                    FOREIGN KEY (event_id) REFERENCES events(event_id),
                    FOREIGN KEY (telegram_user_id) REFERENCES users(telegram_user_id),
                    UNIQUE (event_id, telegram_user_id)
                )
            '''
        )
        await self.connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS administrators (
                    telegram_user_id INTEGER PRIMARY KEY,
                    telegram_username TEXT,
                    organization_id INTEGER DEFAULT 1 REFERENCES organizations(organization_id),
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        )
        await self.connection.execute(
            '''
                CREATE TABLE IF NOT EXISTS organizations (
                    organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_name TEXT NOT NULL,
                    UNIQUE(organization_name)
                )
            '''
        )
        await self.connection.execute(
            '''
                CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id)
            '''
        )
        await self.connection.execute(
            '''
                CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(telegram_user_id)
            '''
        )
        await self.connection.execute(
            '''
                CREATE INDEX IF NOT EXISTS idx_events_active ON events(event_is_active)
            '''
        )
        await self.connection.execute(
            '''
                CREATE INDEX IF NOT EXISTS idx_organization_id ON organizations(organization_id)
            '''
        )

        await self.organization_record_add(organization_name)

        if not await self.administrators_count():
            try:
                for admin_bot in admins_bot:
                    await self.administrators_add(admin_bot, 1)
                    logging.info(f'Adding administrators from file .env, variable: ADMINS')
            except aiosqlite.Error as e:
                logging.error(f"Error the add administrators event: {e}")
                self.connection.close()
                os._exit(1)
            
        if await self.get_events_count(None) == 0:
            try:
                await self.event_add_new(
                    'Название мероприятия!',
                    '66 июня 6666 года',
                    1,
                    False
                )
                logging.info(f'Create a default event!')
            except aiosqlite.Error as e:
                logging.error(f"Error the create a default event: {e}")
                self.connection.close()
                os._exit(1)
        await self.connection.commit()
    
    # endregion

    # region Events

    async def registration_record_add(self, event_id: int, telegram_user_id: int, status: str, nickname: str | None = None, telegram_username: str | None = None, additional_information: str | None = None) -> bool:
        try:
            await self.connection.execute (
                '''
                    INSERT INTO registrations (
                        event_id,       
                        telegram_user_id, 
                        nickname, 
                        telegram_username, 
                        additional_information,
                        status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (event_id, telegram_user_id) DO UPDATE SET
                        nickname = COALESCE(?, nickname),
                        telegram_username = COALESCE(?, telegram_username),
                        additional_information = COALESCE(?, additional_information),
                        status = COALESCE(?, status)
                ''', (event_id, telegram_user_id, nickname, telegram_username, additional_information, status, nickname, telegram_username, additional_information, status)
            )
            await self.connection.commit()
            logging.info(f"User: {telegram_user_id} registering for event: {event_id}")
            return True
        except aiosqlite.Error as e:
            logging.error(f"Registration error: {e}")
            return False

    async def add_registration_user(self, telegram_user_id: int):
        try:
            cursor = await self.connection.execute(
                'SELECT 1 FROM users WHERE telegram_user_id = ?',
                (telegram_user_id,)
            )
            telegram_user_id_exists = await cursor.fetchone()
            if not telegram_user_id_exists:
                await self.connection.execute(
                    'INSERT INTO users (telegram_user_id) VALUES (?)',
                    (telegram_user_id,)
                )
                await self.connection.commit()
                logging.info(f"User: {telegram_user_id} added to database.")
            else:
                logging.info(f"User: {telegram_user_id} already exists.")
        except aiosqlite.Error as e:
            logging.error(f"Adding user to database failed with error: {e}")
            return False
    
    async def event_add_new(self, event_name: str, event_date: str, organization_id: int, event_is_active: bool) -> bool:
        try:
            await self.connection.execute(
                '''
                    INSERT OR IGNORE INTO events (
                        event_name,
                        event_date,
                        organization_id,
                        event_is_active
                        ) VALUES (?, ?, ?, ?)
                ''',
                (event_name, event_date, organization_id, event_is_active,)
            )
            await self.connection.commit()
            return True
        except aiosqlite.Error as e:
            logging.error(f"Adding new event failed with error: {e}")
            return False
    
    async def get_events_count(self, is_active: bool | None = True) -> int:
        query = "SELECT COUNT(*) FROM events"
        params = ()
        if is_active is not None:
            query += " WHERE event_is_active = ?"
            params = (is_active,)
        cursor = await self.connection.execute(query, params)
        result = await cursor.fetchone()
        return result[0]

    async def get_events_count_org(self, organization_id: int) -> int:
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM events WHERE organization_id = ?",
            (organization_id,)
        )
        result = await cursor.fetchone()
        return result[0]

    async def events_list_get(self, page: int | int = 1, per_page: int | int = 1, organization_id: int | int = 1) -> list:
        offset = page * per_page
        cursor = await self.connection.execute(
            '''
                SELECT 
                    event_id, 
                    event_name, 
                    event_date,
                    organization_id,
                    event_is_active
                FROM events 
                WHERE organization_id = ?
                ORDER BY rowid DESC
                LIMIT ? OFFSET ?
            ''',
            (organization_id, per_page, offset)
        )
        return await cursor.fetchall()

    async def events_list_public_get(self, page: int | int = 0, per_page: int | int = 10) -> list:
        offset = page * per_page
        cursor = await self.connection.execute(
            '''
                SELECT 
                    event_id, 
                    event_name, 
                    event_date,
                    event_is_active
                FROM events 
                ORDER BY rowid DESC
                LIMIT ? OFFSET ?
            ''',
            (per_page, offset)
        )
        return await cursor.fetchall()

    async def event_get_details(self, request_event_id: int) -> dict:
        cursor = await self.connection.execute(
            '''
                SELECT
                    event_id,
                    event_name, 
                    event_date,
                    organization_id,
                    event_is_active
                FROM events
                WHERE event_id = ?
            ''',
            (request_event_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None
        
        return {
            'event_id': row['event_id'],
            'event_name': row['event_name'],
            'event_date': row['event_date'],
            'organization_id': row['organization_id'],
            'event_is_active': row['event_is_active']
        }
    
    async def event_update_details(self, event_id: int, new_name: str,  new_date: str,  new_organization_id: int, new_status: int) -> bool:
        try:
            await self.connection.execute(
                '''
                    UPDATE events 
                    SET 
                        event_name = ?,
                        event_date = ?,
                        organization_id = ?,
                        event_is_active = ?
                    WHERE 
                        event_id = ?
                ''',  (new_name, new_date, new_organization_id, new_status, event_id)
            )
            await self.connection.commit()
            return True
        except aiosqlite.Error as e:
            logging.error(f"Update event failed with error: {e}")
            return False

    async def event_get_participants_count(self, event_id: int) -> int:
        cursor = await self.connection.execute(
            'SELECT COUNT(*) FROM registrations WHERE event_id = ?',
            (event_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0

    async def event_get_participants_csv(self, event_id: int) -> str:
        cursor = await self.connection.execute(
            '''
                SELECT 
                    registration_id,
                    event_id,
                    telegram_user_id,
                    nickname,
                    telegram_username,
                    additional_information,
                    reg_date,
                    status
                FROM registrations
                WHERE event_id = ?
                ORDER BY reg_date DESC
            ''',
            (event_id,)
        ) 
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "ID регистрации",
            "ID мероприятия",
            "ID пользователя",
            "Имя/Псевдоним",
            "Никнейм Telegram",
            "Доп. информация",
            "Дата регистрации",
            "Статус"
        ])
        async for row in cursor:
            writer.writerow([
                row['registration_id'],
                row['event_id'],
                row['telegram_user_id'],
                row['nickname'],
                f"@{row['telegram_username']}" if row['telegram_username'] else "-",
                row['additional_information'],
                row['reg_date'],
                row['status']
            ])
        csv_buffer.seek(0)
        return csv_buffer.getvalue()

    async def users_get_list_csv(self) -> str:
        cursor = await self.connection.execute(
            '''
                SELECT 
                    telegram_user_id,
                    join_date
                FROM users
                ORDER BY join_date DESC
            '''
        )
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "User telegram ID",
            "Date first use",
        ])
        async for row in cursor:
            writer.writerow([
                row['telegram_user_id'],
                row['join_date'],
            ])

        csv_buffer.seek(0)
        return csv_buffer.getvalue()

    async def administrators_get_list_csv(self) -> str:
        cursor = await self.connection.execute(
            '''
                SELECT 
                    telegram_user_id,
                    telegram_username,
                    organization_id,
                    join_date
                FROM administrators
                ORDER BY join_date DESC
            '''
        )
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "ID администратора",
            "Username администратора",
            "ID организации",
            "Дата добавления администратора",
        ])
        async for row in cursor:
            writer.writerow([
                row['telegram_user_id'],
                row['telegram_username'],
                row['organization_id'],
                row['join_date'],
            ])
        csv_buffer.seek(0)
        return csv_buffer.getvalue()
    
    async def event_participants_get(self, event_id: int) -> list[int]:
        cursor = await self.connection.execute(
            'SELECT telegram_user_id FROM registrations WHERE event_id = ?', 
            (event_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    
    async def users_list_all_get(self) -> list[int]:
        cursor = await self.connection.execute(
            'SELECT telegram_user_id FROM users'
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    # endregion

    # region Administrators

    async def administrators_add(self, telegram_user_id: int, organization_id: int, telegram_username: str = None) -> bool:
        try:
            await self.connection.execute(
                '''
                INSERT OR REPLACE INTO administrators
                    (telegram_user_id, telegram_username, organization_id)
                VALUES (?, ?, ?)
                ''',
                (telegram_user_id, telegram_username, organization_id)
            )
            await self.connection.commit()
            return True
        except aiosqlite.Error as e:
            logging.error(f"Adding user to administrators failed with error: {e}")
            return False
        
    async def administrators_del(self, telegram_user_id: int) -> bool:
        try:
            await self.connection.execute(
                'DELETE FROM administrators WHERE telegram_user_id = ?',
                (telegram_user_id,)
            )
            await self.connection.commit()
            return self.connection.total_changes > 0
        except aiosqlite.Error as e:
            logging.error(f"Delete user from administrators failed with error: {e}")
            return False
        
    async def administrators_list(self) -> list:
        cursor = await self.connection.execute(
            '''
                SELECT 
                    telegram_user_id,
                    telegram_username,
                    organization_id,
                    join_date
                FROM administrators
                ORDER BY join_date DESC
            '''
        )
        await self.connection.commit()
        return await cursor.fetchall()

    async def administrators_count(self) -> int:
        cursor = await self.connection.execute("SELECT COUNT(*) FROM administrators")
        result = await cursor.fetchone()
        return result[0]
    
    # endregion

    # region Organisations

    async def organization_record_add(self, org_name: str) -> bool:
        try:
            cursor = await self.connection.execute(
                'SELECT 1 FROM organizations WHERE organization_name = ?',
                (org_name,)
            )
            exists = await cursor.fetchone()
            
            if exists:
                await self.connection.execute(
                '''
                    UPDATE organizations 
                    SET organization_name = ?
                    WHERE organization_name = ?
                ''', (org_name, org_name)
                )
                await self.connection.commit()
                action = "updated"
            else:
                await self.connection.execute(
                    '''
                        INSERT INTO organizations (
                            organization_name
                        ) VALUES (?)
                    ''', (org_name,)
                )
                await self.connection.commit()
                action = "added"
            logging.info(f"Organization {action}: [organization_name:{org_name}]")
            return True
        except aiosqlite.Error as e:
            logging.error(f"Action with the organization table failed with an error: {e}")
            return False
    
    async def get_admin_organization(self, telegram_user_id: int) -> int:
        cursor = await self.connection.execute(
            'SELECT organization_id FROM administrators WHERE telegram_user_id = ?',
            (telegram_user_id,)
        )
        result = await cursor.fetchone()
        logging.info(f'telegram_user_id:{telegram_user_id} and result:{result}')
        try:
            return result[0]
        except Exception as e:
            logging.error(f'ERROR:> telegram_user_id:{telegram_user_id} | {e}')
    
    # endregion

db_connection = Database()

async def initialize_database():
    await db_connection.check_database_on_startup()
    await db_connection.initialize_content_database()