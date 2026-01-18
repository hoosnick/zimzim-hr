import asyncio
import sys

from apps.poller import main as poller_main


def main():
    try:
        asyncio.run(poller_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
