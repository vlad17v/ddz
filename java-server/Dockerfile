FROM openjdk:17-jdk-slim
WORKDIR /code
COPY . .
ENTRYPOINT ["java", "-cp", ".:gson-2.10.jar:sqlite-jdbc-3.46.1.3.jar", "web.MultiThreadServer"]
#sqlite-jdbc-3.46.1.3.jar