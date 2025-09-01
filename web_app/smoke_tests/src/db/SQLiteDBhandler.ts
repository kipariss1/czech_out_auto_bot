import Database from "better-sqlite3";
import { smokeTestsDir } from "../index.js";
import path from "path";
import fs from "fs";

type TestUser = {
    id: string;
    language: string;
};

export class SQLiteDBhandler {

    private dbPath: string;
    private db: InstanceType<typeof Database>;

    constructor () {
        this.dbPath = path.join(smokeTestsDir, "..", "..", "src", "db", "local.db")
        this.db = new Database(this.dbPath);
    }

    insertUser(usr: TestUser) {
        const insert = this.db.prepare("INSERT INTO Users (id, language) VALUES (?, ?)");
        insert.run(usr.id, usr.language);
    }


    removeUser() {
        this.db.prepare("DELETE FROM Users").run();
    }

}
