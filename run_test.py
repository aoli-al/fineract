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
    subprocess.call("jenv local 16", shell=True)
    command = [f"-DPhosphor.INSTRUMENTATION_CLASSPATH={INSTRUMENTATION_CLASSPATH}",
               f"-DPhosphor.ORIGIN_CLASSPATH={ORIGIN_CLASSPATH}",
               "-cp", PHOSPHOR_JAR_PATH, "edu.columbia.cs.psl.phosphor.Instrumenter",
               "fineract-provider/build/libs/fineract-provider.jar", INSTRUMENTATION_FOLDER_NAME,
               "-taintTagFactory", "al.aoli.exchain.phosphor.instrumenter.DynamicSwitchTaintTagFactory"
               ]
    if debug:
        command.insert(
            0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    subprocess.call(["java"] + command, cwd=DIR)
    command = [f"-DPhosphor.INSTRUMENTATION_CLASSPATH={HYBRID_CLASSPATH}",
               "-cp", PHOSPHOR_JAR_PATH, "edu.columbia.cs.psl.phosphor.Instrumenter",
               "fineract-provider/build/libs/fineract-provider.jar", HYBRID_FOLDER_NAME,
               "-taintTagFactory", "al.aoli.exchain.phosphor.instrumenter.FieldOnlyTaintTagFactory",
               "-postClassVisitor", "al.aoli.exchain.phosphor.instrumenter.UninstrumentedOriginPostCV"
               ]
    if debug:
        command.insert(
            0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    subprocess.call(["java"] + command, cwd=DIR)


@main.command(name="origin")
@click.option('--debug', default=False, help='Enable debugging.')
def origin(debug: bool):
    pre()
    command = ["-jar", f"fineract-provider/build/libs/fineract-provider.jar"]
    if debug:
        command.insert(
            0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    cmd = subprocess.Popen(["java"] + command, cwd=DIR)
    time.sleep(20)
    #  wait_up(cmd)
    post('origin')
    cmd.kill()


def pre():
    subprocess.call("jenv local 11", shell=True)
    subprocess.call("docker rm -f mysql-5.7", shell=True)
    subprocess.call(
        "docker run --name mysql-5.7 -p 3306:3306 -e MYSQL_ROOT_PASSWORD=mysql -d mysql:5.7", shell=True)
    time.sleep(10)
    subprocess.call("./gradlew createDB -PdbName=fineract_tenants", shell=True)
    subprocess.call("./gradlew createDB -PdbName=fineract_default", shell=True)


def post(type):
    subprocess.call(
        "./gradlew integrationTest --tests org.apache.fineract.integrationtests.HookIntegrationTest.shouldSendOfficeCreationNotification", shell=True)


def wait_up(cmd):
    for line in cmd.stdout:
        line = line.decode("utf-8")
        print(line)
        if "org.apache.fineract.ServerApplication    : Started ServerApplication" in line:
            break


@main.command(name="hybrid")
@click.option('--debug', default=False, help='Enable debugging.')
def hybrid(debug: bool):
    pre()
    args = [HYBRID_JAVA_EXEC,
            f"-javaagent:{PHOSPHOR_AGENT_PATH}=taintTagFactory=al.aoli.exchain.phosphor.instrumenter.FieldOnlyTaintTagFactory,postClassVisitor=al.aoli.exchain.phosphor.instrumenter.UninstrumentedOriginPostCV",
            f"-javaagent:{RUNTIME_JAR_PATH}=hybrid:{HYBRID_CLASSPATH}",
            f"-agentpath:{NATIVE_LIB_PATH}=exchain:Lorg/apache/fineract",
            "-jar",
            f"{HYBRID_FOLDER_NAME}/fineract-provider.jar",
            ]
    if debug:
        args.insert(1, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    print(" ".join(args))
    cmd = subprocess.Popen(args, cwd=DIR)
    time.sleep(100)
    #  wait_up(cmd)
    post("hybrid")
    cmd.kill()


@main.command(name="static")
def static():
    pre()
    args = ["java",
                            f"-javaagent:{RUNTIME_JAR_PATH}=static:{INSTRUMENTATION_CLASSPATH}",
                            f"-agentpath:{NATIVE_LIB_PATH}=exchain:Lorg/apache/fineract",
                            "-jar",
                            f"fineract-provider/build/libs/fineract-provider.jar",
                            ]
    #  cmd = subprocess.Popen(args,
                          #  cwd=DIR, stdout=subprocess.PIPE)
    cmd = subprocess.Popen(args, cwd=DIR)
    #  wait_up(cmd)
    time.sleep(100)
    post("static")
    cmd.kill()


@main.command(name="dynamic")
@click.option('--debug', default=False, help='Enable debugging.')
def dynamic(debug: bool):
    pre()
    args = [
        "--add-opens=java.base/java.lang=ALL-UNNAMED",
        f"-javaagent:{PHOSPHOR_AGENT_PATH}",
        f"-javaagent:{RUNTIME_JAR_PATH}=dynamic:{INSTRUMENTATION_CLASSPATH}",
        f"-agentpath:{NATIVE_LIB_PATH}=exchain:Lorg/apache/fineract",
        "-jar",
        f"{INSTRUMENTATION_FOLDER_NAME}/fineract-provider.jar",
    ]
    if debug:
        args.insert(
            0, "-agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005")
    cmd = subprocess.Popen([INSTRUMENTED_JAVA_EXEC] + args,
                           cwd=DIR)
    time.sleep(300)
    #  wait_up(cmd)
    post('dynamic')
    cmd.kill()


if __name__ == '__main__':
    main()
