#!/usr/bin/env sh
# Gradle wrapper script
# If gradle wrapper jar is missing, fall back to system gradle

GRADLE_OPTS="${GRADLE_OPTS:-""}"
DEFAULT_JVM_OPTS="${DEFAULT_JVM_OPTS:-""}"

# Determine the Java command to use to start the JVM.
if [ -n "$JAVA_HOME" ] ; then
    JAVACMD="$JAVA_HOME/bin/java"
    if [ ! -x "$JAVACMD" ] ; then
        die "ERROR: JAVA_HOME is set to an invalid directory: $JAVA_HOME"
    fi
else
    JAVACMD="java"
fi

# Use gradle wrapper jar if available, otherwise use system gradle
WRAPPER_JAR="$(dirname "$0")/gradle/wrapper/gradle-wrapper.jar"
if [ -f "$WRAPPER_JAR" ]; then
    exec "$JAVACMD" -classpath "$WRAPPER_JAR" org.gradle.wrapper.GradleWrapperMain "$@"
else
    exec gradle "$@"
fi
