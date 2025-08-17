package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"os"
)

func main() {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error generating RSA key: %v\n", err)
		os.Exit(1)
	}

	privDER := x509.MarshalPKCS1PrivateKey(privateKey)

	privBlock := &pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: privDER,
	}

	privFile, err := os.Create("private_key.pem")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating private_key.pem: %v\n", err)
		os.Exit(1)
	}
	defer privFile.Close()

	if err := pem.Encode(privFile, privBlock); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing private_key.pem: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Private key saved in private_key.pem")

	pubDER, err := x509.MarshalPKIXPublicKey(&privateKey.PublicKey)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error serializing public key: %v\n", err)
		os.Exit(1)
	}

	pubBlock := &pem.Block{
		Type:  "PUBLIC KEY",
		Bytes: pubDER,
	}

	pubFile, err := os.Create("public_key.pem")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating public_key.pem: %v\n", err)
		os.Exit(1)
	}
	defer pubFile.Close()

	if err := pem.Encode(pubFile, pubBlock); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing public_key.pem: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Public key saved in public_key.pem")
}
