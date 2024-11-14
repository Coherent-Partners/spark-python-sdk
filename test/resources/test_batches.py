import pytest
from cspark.sdk import BatchChunk, SparkSdkError, create_chunks

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
    inputs = [[1, 20, 65], [2, 74, 73], [3, 20, 65], [4, 34, 73], [5, 62, 62]]  # 5 rows
    chunks = create_chunks(inputs, chunk_size=3)

    assert len(chunks) == 2
    assert chunks[0].size == 3
    assert chunks[1].size == 2

    assert chunks[0].data.inputs == [[1, 20, 65], [2, 74, 73], [3, 20, 65]]
    assert chunks[1].data.inputs == [[4, 34, 73], [5, 62, 62]]
    assert all(chunk.data.parameters == {} for chunk in chunks)
    assert all(chunk.data.summary is None for chunk in chunks)
