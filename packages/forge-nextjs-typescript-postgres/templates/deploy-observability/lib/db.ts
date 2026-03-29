import { PrismaClient } from "@prisma/client";

declare global {
  var __forgePrisma__: PrismaClient | undefined;
}

export const db = globalThis.__forgePrisma__ ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalThis.__forgePrisma__ = db;
}
