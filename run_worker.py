import asyncio

from apps.worker import app


def main():
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
