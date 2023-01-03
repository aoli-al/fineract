#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import click
import time
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
    command = [f"-DPhosphor.INSTRUMENTATION_CLASSPATH={INSTRUMENTATION_CLASSPATH}",
               f"-DPhosphor.ORIGIN_CLASSPATH={ORIGIN_CLASSPATH}",
               "-cp", PHOSPHOR_JAR_PATH, "edu.columbia.cs.psl.phosphor.Instrumenter",
               "fineract-provider/build/libs/fineract-provider.jar", INSTRUMENTATION_FOLDER_NAME]
    if debug:
        command.insert(0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    subprocess.call(["java"] + command, cwd=DIR)


@main.command(name="origin")
@click.option('--debug', default=False, help='Enable debugging.')
def origin(debug: bool):
    # pre()
    command = ["-jar", f"fineract-provider/build/libs/fineract-provider.jar"]
    if debug:
        command.insert(0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    cmd = subprocess.Popen(["java"] + command, cwd=DIR, stdout=subprocess.PIPE)
    wait_up(cmd)
    post()
    cmd.kill()


def pre():
    subprocess.call("docker rm -f mysql-5.7", shell=True)
    subprocess.call("docker run --name mysql-5.7 -p 3306:3306 -e MYSQL_ROOT_PASSWORD=mysql -d mysql:5.7", shell=True)
    time.sleep(10)
    subprocess.call("./gradlew createDB -PdbName=fineract_tenants", shell=True)
    subprocess.call("./gradlew createDB -PdbName=fineract_default", shell=True)


def post():
    subprocess.call(
        "./gradlew integrationTest --tests org.apache.fineract.integrationtests.HookIntegrationTest.shouldSendOfficeCreationNotification", shell=True)

def wait_up(cmd):
    for line in cmd.stdout:
        print(line)
        if "org.apache.fineract.ServerApplication    : Started ServerApplication" in line.decode("utf-8"):
            break


@main.command(name="static")
def static():
    pre()
    cmd = subprocess.Popen(["java",
                            f"-javaagent:{RUNTIME_JAR_PATH}=static:{INSTRUMENTATION_CLASSPATH}",
                            f"-agentpath:{NATIVE_LIB_PATH}=exchain:Lorg/apache/fineract",
                            "-jar",
                            f"{INSTRUMENTATION_FOLDER_NAME}/fineract-provider.jar",
                            ],
                            cwd=DIR, stdout=subprocess.PIPE)
    wait_up(cmd)
    post()
    cmd.kill()
    args = ["./gradlew", "static-analyzer:run", f"--args={ORIGIN_CLASSPATH} {DIR}/static-results {ORIGIN_CLASSPATH}"]
    subprocess.call(args, cwd=os.path.join(DIR, "../.."))


@main.command(name="dynamic")
def dynamic():
    pre()
    cmd = subprocess.Popen([INSTRUMENTED_JAVA_EXEC,
                            f"-javaagent:{PHOSPHOR_AGENT_PATH}",
                            f"-javaagent:{RUNTIME_JAR_PATH}=dynamic:{INSTRUMENTATION_CLASSPATH}",
                            f"-agentpath:{NATIVE_LIB_PATH}=exchain:Lorg/apache/fineract",
                            "-jar",
                            f"{INSTRUMENTATION_FOLDER_NAME}/fineract-provider.jar",
                            ],
                            cwd=DIR, stdout=subprocess.PIPE)
    wait_up(cmd)
    post()
    cmd.kill()


if __name__ == '__main__':
    main()
