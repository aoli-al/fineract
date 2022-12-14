#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import click
DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(DIR, ".."))
from commons import *


@click.group(name="mode")
def main():
    pass


@main.command(name="build")
def build():
    subprocess.call(["./gradlew", "bootJar"], cwd=DIR)

@main.command(name="instrument")
@click.option('--debug', default=False, help='Enable debugging.')
def instrument(debug: bool):
    command = [f"-DPhosphor.INSTRUMENTED_CLASSPATH={INSTRUMENTATION_CLASSPATH}",
               "-cp", PHOSPHOR_JAR_PATH, "edu.columbia.cs.psl.phosphor.Instrumenter",
               "fineract-provider/build/libs/fineract-provider.jar", INSTRUMENTATION_FOLDER_NAME]
    if debug:
        command.insert(0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    subprocess.call(["java"] + command, cwd=DIR)


@main.command(name="origin")
@click.option('--debug', default=False, help='Enable debugging.')
def origin(debug: bool):
    command = ["-jar", f"fineract-provider/build/libs/fineract-provider.jar"]
    if debug:
        command.insert(0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    subprocess.call(["java"] + command, cwd=DIR)


def pre():
    pass

def post():
    pass

def is_up():
    pass


@main.command(name="dynamic")
def dynamic():
    subprocess.call([INSTRUMENTED_JAVA_EXEC,
                     "-jar",
                     f"{INSTRUMENTATION_FOLDER_NAME}/fineract-provider.jar",
                     f"-javaagent:{PHOSPHOR_AGENT_PATH}",
                     f"-javaagent:{RUNTIME_JAR_PATH}={INSTRUMENTATION_CLASSPATH}",
                     f"-agentpath:{NATIVE_LIB_PATH}=taint",
                     "org.apache.hadoop.hdfs.server.namenode.TestCheckpoint"])


if __name__ == '__main__':
    main()
