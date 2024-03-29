# run the inference flow
INFERENCE_OUTPUT=$(pf run create --flow ./board-game-chat/flow.dag.yaml --data ./evaluations/questions.jsonl --column-mapping chat_history='${data.chat_history}' query='${data.query}' mode='${data.mode}')
INFERENCE_ID=$(echo "$INFERENCE_OUTPUT" | grep -oP '"name": "\K[^"]+')

# run the eval flow
EVAL_OUTPUT=(pf run create --flow ./board-game-chat-eval/flow.dag.yaml --data ./evaluations/questions.jsonl --column-mapping question='${data.query}' context='no-context' answer='${run.outputs.answer}' --run $INFERENCE_ID)
EVAL_ID=$(echo "$EVAL_OUTPUT" | grep -oP '"name": "\K[^"]+')

# output the eval flow details
pf run show-details -n $EVAL_ID