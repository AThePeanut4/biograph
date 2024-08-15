#!/usr/bin/env python3

import uvicorn
import yaml


def main():
    with open("config/uvicorn.yml", "r") as f:
        cfg = yaml.safe_load(f)

    uvicorn.run("biograph.main:api", **cfg)


if __name__ == "__main__":
    main()
