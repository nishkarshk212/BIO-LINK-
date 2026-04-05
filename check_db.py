import aiosqlite
import asyncio

async def check_settings():
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT chat_id, edit_checker, edit_apply_to FROM settings") as cur:
            rows = await cur.fetchall()
            if rows:
                print(f"Found {len(rows)} group(s):")
                for row in rows:
                    print(f"\nChat ID: {row[0]}")
                    print(f"  Edit Checker: {'✅ ENABLED' if row[1] == 1 else '❌ DISABLED'}")
                    print(f"  Edit Apply To: {row[2]}")
            else:
                print("No groups configured.")

if __name__ == "__main__":
    asyncio.run(check_settings())
