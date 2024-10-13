from deezer_arl.consumer.consumer import Consumer
from deezer_arl.consumer.json import Json
from deezer_arl.consumer.file import File

Consumers = {
    'json': Json,
    'file': File
}
