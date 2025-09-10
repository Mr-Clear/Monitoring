#!/home/user/Monitoring/venv/bin/python

import json

from dataclasses import dataclass
from subprocess import check_output, CalledProcessError, PIPE
from pprint import pprint

@dataclass
class DockerImage:
    repository: str
    tag: str
    id: str
    created: str
    size: str

    @staticmethod
    def from_json(j: str):
        return DockerImage(
            repository=j['Repository'],
            tag=j['Tag'],
            id=j['ID'],
            created=j['CreatedAt'],
            size=j['Size']
        )

@dataclass
class DockerContainer:
    id: str
    image: str
    command: str
    created: str
    state: str
    ports: str
    names: str

    @staticmethod
    def from_json(j: str):
        return DockerContainer(
            id=j['ID'],
            image=j['Image'],
            command=j['Command'],
            created=j['CreatedAt'],
            state=j['State'],
            ports=j['Ports'],
            names=j['Names']
        )


if __name__ == "__main__":
    try:
        output = check_output(['ssh', 'www.klierlinge.de', 'docker', 'ps', '-a', '--format', 'json'], stderr=PIPE)
    except CalledProcessError as e:
        print(e.output)
        exit(1)

    containers = [DockerContainer.from_json(json.loads(line)) for line in output.decode().split('\n') if line]


    try:
        output = check_output(['ssh', 'www.klierlinge.de', 'docker', 'images', '--format', 'json'], stderr=PIPE)
    except CalledProcessError as e:
        print(e.output)
        exit(1)
    
    images = [DockerImage.from_json(json.loads(line)) for line in output.decode().split('\n') if line]

    for container in containers:
        if container.image not in [image.repository for image in images]:
            print(f"Container {container.names} is using an image that is not available locally: {container.image}")
