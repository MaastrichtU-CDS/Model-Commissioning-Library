echo "Build image"
docker build -t stiphout_model_image ./

echo "============================================="
echo "Start container"
docker run -d --rm \
    --name "stiphout_model" \
    -v $(pwd)/run.py:/run.py \
    -v $(pwd)/requirements.txt:/requirements.txt \
    -p 5000:5000 \
    stiphout_model_image

sleep 5

echo "============================================="
echo "Execute model"
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"cT": 3, "cN": 1, "tLength": 5}' \
  http://localhost:5000/

echo ""
echo "============================================="
echo "Teardown of container"
docker stop stiphout_model

echo "============================================="
echo "Teardown of image"
docker rmi stiphout_model_image