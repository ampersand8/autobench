package main

import (
	"flag"
	"fmt"
	"strings"
	"time"

	"github.com/ampersand8/bench"
	"github.com/ampersand8/bench/requester"
)

func main() {
	var cluster = flag.String("cluster", "nats", "Choose cluster to test [kafka, nats]")
	var url = flag.String("url", "nats://localhost:4222", "URL to Message Service")
	var requestRate = flag.Uint64("rate", 10000, "Requests per second")
	var connections = flag.Uint64("connections", 1, "Number of concurrent connections")
	var duration = flag.Duration("duration", 30*time.Second, "Duration in seconds")
	var payload = flag.Int("payload", 500, "Payload size in bytes")
	var outputfile = flag.String("out", "bench.txt", "Output file")
	flag.Parse()
	var r bench.RequesterFactory
	fmt.Printf("Rate: %d", *requestRate)

	switch *cluster {
	case "kafka":
		r = &requester.KafkaRequesterFactory{
			URLs:        strings.Split(*url, ","),
			PayloadSize: *payload,
			Topic:       "benchmark",
		}
	default:
		r = &requester.NATSRequesterFactory{
			URL:         *url,
			PayloadSize: *payload,
			Subject:     "benchmark",
		}
	}

	benchmark := bench.NewBenchmark(r, *requestRate, *connections, *duration, 0)
	summary, err := benchmark.Run()
	if err != nil {
		panic(err)
	}

	fmt.Println(summary)
	summary.GenerateLatencyDistribution(nil, *outputfile)
}
