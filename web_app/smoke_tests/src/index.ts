import path from "path"
import { SQLiteDBhandler } from "./db/SQLiteDBhandler"
import { CipherHandler } from './security/CipherHandler';
import { fileURLToPath } from "url";

export const smokeTestsDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
export const sqliteDBhandler = new SQLiteDBhandler();
export const cipherHandler = new CipherHandler();
