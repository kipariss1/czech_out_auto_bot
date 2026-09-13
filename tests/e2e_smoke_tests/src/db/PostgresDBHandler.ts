import { Client } from "pg";

type TestUser = {
    id: number;
    telegramId: number;
};

export class PostgresDBHandler {

    private client: Client;

    constructor () {
        this.client = new Client({
            host: process.env.TEST_POSTGRES_HOST ?? "localhost",
            port: Number(process.env.TEST_POSTGRES_PORT ?? 5433),
            user: process.env.POSTGRES_USER,
            password: process.env.POSTGRES_PASSWORD,
            database: process.env.POSTGRES_DB,
        });
    }

    async connect() {
        await this.client.connect();
    }

    async disconnect() {
        await this.client.end();
    }

    async insertUser(usr: TestUser) {
        await this.client.query(
            'INSERT INTO "Users" (id, telegram_id) VALUES ($1, $2)',
            [usr.id, usr.telegramId],
        );
    }

    async removeUsers() {
        await this.client.query('DELETE FROM "Users"');
    }

    async removeSearches() {
        await this.client.query('DELETE FROM "Car_Searches"');
    }

    async cleanDB() {
        await this.removeSearches();
        await this.removeUsers();
    }
}
