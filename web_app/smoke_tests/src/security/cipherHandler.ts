import * as fernet from 'fernet';

export class CipherHandler {
  private secret: fernet.Secret;
  private key: string;

  constructor() {
    const envKey = process.env.CIPHER_KEY;
    if (!envKey) {
      throw new Error("CIPHER_KEY is not set in environment variables");
    }

    this.key = envKey;
    this.secret = new fernet.Secret(this.key);
  }

  encode(str2encode: string | Buffer): string {
    const input = Buffer.isBuffer(str2encode)
      ? str2encode.toString("utf8")
      : str2encode;

    const token = new fernet.Token({
      secret: this.secret,
      time: Date.now(),
    });

    return token.encode(input);
  }

  decode(str2decode: string): string {
    const token = new fernet.Token({
      secret: this.secret,
      token: str2decode,
      ttl: 0, // без ограничения времени
    });

    return token.decode();
  }

  urlSafeEncode(str2encode: string | Buffer): string {
    return encodeURIComponent(this.encode(str2encode));
  }

  decodeFromUrl(str2decode: string): string {
    return this.decode(decodeURIComponent(str2decode));
  }
}
