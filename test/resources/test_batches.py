import pytest
from cspark.sdk import BatchChunk, Client, SparkSdkError, create_chunks

RAW_STRING = """
{
  "chunks": [
    {
      "id": "0001",
      "size": 2,
      "data": {
        "inputs": [
          ["sale_id", "price", "quantity"],
          [1, 20, 65],
          [2, 74, 73]
        ],
        "parameters": {"tax": 0.1}
      }
    },
    {
      "size": 1,
      "data": {
        "inputs": [
          ["sale_id", "price", "quantity"],
          [3, 20, 65]
        ],
        "summary": {
          "ignore_error": false,
          "aggregation": [{"output_name": "total", "operator": "SUM"}
          ]
        }
      }
    }
  ]
}
"""


def test_batch_chunk_throw_sdk_error_if_it_fails_parse_raw_string():
    with pytest.raises(SparkSdkError):
        BatchChunk.from_str('invalid-json')


def test_batch_chunk_can_parse_raw_string_into_object():
    chunks = BatchChunk.from_str(RAW_STRING)
    assert len(chunks) == 2
    assert chunks[0].id == '0001'
    assert chunks[0].size == 2
    assert chunks[0].data.inputs == [['sale_id', 'price', 'quantity'], [1, 20, 65], [2, 74, 73]]
    assert chunks[0].data.parameters == {'tax': 0.1}
    assert chunks[0].data.summary is None

    assert chunks[1].id is not None
    assert chunks[1].size == 1
    assert chunks[1].data.inputs == [['sale_id', 'price', 'quantity'], [3, 20, 65]]
    assert chunks[1].data.parameters == {}
    assert chunks[1].data.summary == {
        'ignore_error': False,
        'aggregation': [{'output_name': 'total', 'operator': 'SUM'}],
    }


def test_batch_chunk_can_parse_raw_array_into_object():
    # key 'chunks' is optional
    raw = b'[{"id": "0042", "data": {"inputs": [["sale_id", "price", "quantity"], [41, 42, 43]]}}]'
    chunks = BatchChunk.from_str(raw)

    assert len(chunks) == 1
    assert chunks[0].id == '0042'
    assert chunks[0].data.inputs == [['sale_id', 'price', 'quantity'], [41, 42, 43]]
    assert chunks[0].data.parameters == {}
    assert chunks[0].data.summary is None


def test_create_chunks_distribute_input_dataset_evenly():
    headers = ['sale_id', 'price', 'quantity']
    inputs = [[1, 20, 65], [2, 74, 73], [3, 20, 65], [4, 34, 73], [5, 62, 62]]  # 5 rows
    dataset = [headers] + inputs  # expecting JSON array format.
    chunks = create_chunks(dataset, chunk_size=3)

    assert len(chunks) == 2
    assert chunks[0].size == 3
    assert chunks[1].size == 2

    assert chunks[0].data.inputs == [['sale_id', 'price', 'quantity'], [1, 20, 65], [2, 74, 73], [3, 20, 65]]
    assert chunks[1].data.inputs == [['sale_id', 'price', 'quantity'], [4, 34, 73], [5, 62, 62]]
    assert all(chunk.data.parameters == {} for chunk in chunks)
    assert all(chunk.data.summary is None for chunk in chunks)


def test_batches_can_create_batch_pipeline_from_start_to_finish(server):
    batches = Client(base_url=server.url, api_key='open', logger=False).batches

    batch = batches.create('f/s', min_runners=100, runners_per_vm=4, accuracy=0.9)
    assert batch.status == 200
    assert batch.data['object'] == 'batch'
    assert batch.data['id'] == 'batch_uuid'

    pipeline = batches.of(batch.data['id'])
    assert pipeline.is_disposed is False
    assert pipeline.state == 'open'
    assert pipeline.stats == {'records': 0, 'chunks': 0}

    with pytest.raises(SparkSdkError):
        # we should always push some data
        pipeline.push()

    submission = pipeline.push(raw=RAW_STRING)
    assert pipeline.stats == {'records': 3, 'chunks': 2}
    assert submission.status == 200
    assert submission.data['record_submitted'] == 3

    with pytest.raises(SparkSdkError):
        # pipeline can determine if chunk id already exists
        pipeline.push(raw=RAW_STRING, if_chunk_id_duplicated='throw')

    results = pipeline.pull(2)
    assert results.status == 200
    data = results.data['data']
    assert len(data) == 2
    assert len(data[0]['outputs'] + data[1]['outputs']) == 3  # 2+1=3 outputs

    pipeline.dispose()
    assert pipeline.is_disposed is True

    with pytest.raises(SparkSdkError):
        # pipeline can't get canceled if it's already disposed of.
        pipeline.cancel()

    pipeline.close()
    batches.close()
