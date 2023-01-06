python3 run_test.py origin > /tmp/fineract.out &
pid=$!
sleep 10
./gradlew --rerun-tasks integrationTest
./gradlew --rerun-tasks integrationTest
pkill -P $pid
python3 run_test.py static > /tmp/fineract.out &
pid=$!
sleep 30
echo "First"
./gradlew --rerun-tasks integrationTest
echo "Second"
./gradlew --rerun-tasks integrationTest
pkill -P $pid
python3 run_test.py hybrid > /tmp/fineract.out &
pid=$!
sleep 30
./gradlew --rerun-tasks integrationTest
./gradlew --rerun-tasks integrationTest
pkill -P $pid
python3 run_test.py dynamic > /tmp/fineract.out &
pid=$!
sleep 240
./gradlew --rerun-tasks integrationTest
./gradlew --rerun-tasks integrationTest
pkill -P $pid
