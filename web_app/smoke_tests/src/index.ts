import path from "path"
import { SQLiteDBhandler } from "./db/SQLiteDBhandler.js"
import { CipherHandler } from './security/CipherHandler.js';
import { fileURLToPath } from "url";

export const smokeTestsDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
export const sqliteDBhandler = new SQLiteDBhandler();
export const cipherHandler = new CipherHandler();
