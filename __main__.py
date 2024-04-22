import pulumi
import pandas as pd
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.core.v1 import Namespace, Service, ServiceSpecArgs, ServicePortArgs, ContainerArgs, ContainerPortArgs, EnvVarArgs
import pulumi_docker as docker
#from pulumi_docker import ContainerPortArgs

# most helpful: https://www.pulumi.com/ai/conversations/c78f7456-5403-47b3-bc11-ab6ebc9474ff
# Create a Pulumi configuration object
config = pulumi.Config()
model_container_port = config.get_int('modelContainerPort')


# Docker image names for the vector database
vector_db_image = "chromadb/chroma"


# Kubernetes Namespace where the resources will be deployed
app_namespace = Namespace("rag-model-service",
    metadata={"name": "rag-model-service"},
)

#####################
# deploy db         #
#####################

# Deployment for the vector database
vector_db_deployment = Deployment("vector-db-deployment",
    metadata={
        "namespace": app_namespace.metadata["name"],
    },
    spec={
        "selector": {"matchLabels": {"app": "vector-db"}},
        "replicas": 1,
        "template": {
            "metadata": {"labels": {"app": "vector-db"}},
            "spec": {
                "containers": [{
                    "name": "vector-db",
                    "image": vector_db_image,
                }],
            },
        },
    },
)

# Service to expose the vector database
vector_db_service = Service("vector-db-service",
    metadata={
        "namespace": app_namespace.metadata["name"],
    },
    spec={
        "selector": {"app": "vector-db"},
        "ports": [{"port": 8000}], #vector_db_image default port
        "type": "ClusterIP",
    },
)

#####################
# build model image #
#####################

image = docker.Image("rag-model",
    build=docker.DockerBuildArgs(
        context='model',
        dockerfile='model/Dockerfile',
        args = {
            'no_cache': 'true',
        }
    ),
    image_name='docker.io/dzorlu/generative-model:latest',
    skip_push=False
)

# app_name = app_namespace.metadata['name'].apply(lambda name: f"{name}")
# val = vector_db_service.metadata["name"].apply(
#                                 lambda name: f"{name}.{app_name}.svc.cluster.local:{8000}"
#                             )


combined_name = pulumi.Output.all(
    app_namespace.metadata["name"], vector_db_service.metadata["name"]
).apply(
    lambda names: f"{names[1]}.{names[0]}.svc.cluster.local:8000"
)

# Deployment for the generative model with the VECTOR_DB_SERVICE_HOST environment variable
model_deployment = Deployment("model-deployment",
    metadata={
        "namespace": app_namespace.metadata["name"],
    },
    spec={
        "selector": {"matchLabels": {"app": "model"}},
        "replicas": 1,
        "template": {
            "metadata": {"labels": {"app": "model"}},
            "spec": {
                "containers": [
                    ContainerArgs(
                        name="generative-model",
                        image=image.base_image_name,
                        ports=[ContainerPortArgs(container_port=8080)],
                        env= [{
                            "name": "VECTOR_DB_SERVICE_HOST",
                            "value": combined_name,
                        }])
                    ],

            },
        },
    },
)


model_service = Service("model-service",
    metadata={
        "namespace": app_namespace.metadata["name"],
    },
    spec=ServiceSpecArgs(
        selector = {"app": "model"},
        ports= [
            ServicePortArgs(
                port=8080, # The port that the service will serve on
                target_port=8080 # The port on the container to route to
            )
        ],
        type= "ClusterIP",
    )
)

vector_db_url = vector_db_service.metadata["name"]
model_service_url = model_service.metadata["name"]

# # Export the URLs for both services
pulumi.export("vector_db_url", vector_db_url)
pulumi.export("model_url", model_service_url)