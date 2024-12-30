# A17 - MotorIST Project Report

## 1. Introduction

The MotorIST project is a project that aims to provide a secure and efficient way to manage remote car configurations, such as close/open the car, configure the AC and check the battery level. This is done by a user application installer on the users computer/mobile. Additionally, and to maintain the car up to date, the car also allows for firmware updates from the manufacturer and test from the mechanic.

### 1.1. Protection Goals

Due to all the communication with the car being sensitive, the MotorIST project must be secure. The base protection goals of this project are:

- \[SR1: Confidentiality\] The car configurations can only be seen by the car owner.
- \[SR2: Integrity 1\] The car can only accept configurations sent by the car owner.
- \[SR3: Integrity 2\] The car firmware updates can only be sent by the car manufacturer.
- \[SR4: Authentication\] The car manufacture cannot deny having sent firmware updates.

### 1.2. Security Challenge

The security challenge of this project is to ensure the following:

- \[SRB1: data privacy\] The mechanic cannot see the user configurations, even when he has the car key.
- \[SRB2: authorization\] The mechanic (when authenticated) can change any parameter of the car, for testing purposes.
- \[SRB3: data authenticity\] The user can verify that the mechanic performed all the tests to the car.

For this, it is also necessary to implement a maintenance mode on the car, which is set by the user. In this mode the car is set to the default configuration.

### 1.3. Secure Documents

The communication with the car is done using a JSON document which will have the configurations to be set on the car. Since this document is sensitive, it must be protected to ensure the confidentiality, integrity and authenticity of the data. For this, we will be using the custom library that we implemented, `cryptolib`, which will be explained in the next sections.

## 2. Project Development

### 2.1 Assumptions

Due to the nature of the project, we had to make some assumptions to simplify the implementation of the project. These assumptions are:

- We assume that the car key corresponds to the key of the car owner.
- We assume that the car battery always starts at 100%, and the battery level is reduced by 5% for each 10 configurations sent to the car.
- We assume that the car has a default configuration that is set when the maintenance mode is activated.

### 2.2. Secure Documents Library

#### 2.2.1. Design

MotorIST's custom cryptographic library is designed to protect, verify, and unprotect documents. Document protection ensures confidentiality, integrity, and authenticity. The following structure was created to achieve these goals.

##### 2.2.1.1. Confidentiality

To ensure that sensitive information is kept private and only accessible to authorized individuals or systems, this is, to ensure confidentiality, the document is encrypted using the ChaCha20Poly1305 algorithm. This algorithm is an authenticated encryption with associated data (AEAD) algorithm, meaning that it provides both data confidentiality and data authenticity.

When we were thinking of which algorithm to use, we were first thinking of using AES, but we decided to use ChaCha20Poly1305 because it is optimized for software performance, making it faster than AES without hardware support. It also a [great choice](https://ieeexplore.ieee.org/document/7927078) on IoT devices, and embedded systems, which is the case of the car.

The ChaCha20-Poly1305 algorithm takes as input a 256-bit key and a 96-bit nonce to encrypt a plaintext. It is important to note that, to ensure true randomness, the nonce must be generated using a cryptographically secure random number generator. For this, we used the `token_bytes` method from the `secrets` module from Python, as it is the [documentation's recommendation](https://docs.python.org/3/library/secrets.html) for generating cryptographically secure random numbers.

##### 2.2.1.2. Integrity

Acho que isto tem a ver com a parte dos CAs? "\[SR2: Integrity 1\] The car can only accept configurations sent by the car owner; \[SR3: Integrity 2\] The car firmware updates can only be sent by the car manufacturer." @girao esta parte ns mm qual a justifacao mais correta a dar, mas aposto em CAs.

##### 2.2.1.3. Authenticity

To ensure authenticity and non-repudiation, which means that the person who appears to have performed an action is indeed the one who did it, we use asymmetric cryptography. For example, the case of the car manufacturer, the firmware is signed using the manufacturer's private key. This signature is then verified by the car using the manufacturer's public key.

@girao agora nao tenho a certeza se a justifacação aqui deva ser asymetric keys ou se falo em CAs.

#### 2.2.2. Document Structure

An unprotected document is a JSON object with the following structure:

```json
{
    "carId": 1,
    "user": "user1",
    "configuration": {
        "ac": true,
        "driver_door": "closed",
        "tire_pressure": {
            "1": "1psi",
            "2": "3psi",
            "3": "7psi",
            "4": "1000psi"
        },
        "battery": "100%"
    },
   
    "firmware": "2"

}
```

Once the document is protected, it is transformed into a JSON object with the following structure:

```json
{
    "carId": 1,
    "user": "user1",
    "configuration": {
        "nonce": "rh8vYjTDPfqVnpbU",
        "ciphertext": "Zms6TnhM0FB+e7Ci+K3UNmz2N04sN4nx9Wto7vRRV9n5kIlMHPb8S9EVXYVnEEHbWvq5DVIjFFkjtPj+1eK3DBIlp8nVbK4ukL99Ikq1qV3zBHOS3QwEF3GZj1M2mFJvIGV99qYn+91VRS4IlNFCmx8rFiSy0HNxbpuyGsPD1mNkN9Vj9DSh1NgdggY5wvUJlaM="
    },
    "firmware": {
        "nonce": "rh8vYjTDPfqVnpbU",
        "ciphertext": "P3t5WuC0YYkF4Mr+cUxzjm1Q7A=="
    }
}
```

#### 2.2.3. Implementation

We implemented the `cryptolib` library in Python as the project's main programming language is Python. By using this programming language, we can easily integrate the library with the rest of the project.

To help the implementation of the cryptographic operations, we used some external cryptographic libraries, such as `cryptography`, `hashlib`, `base64` and `secrets`.

To ensure that the library is robust and easier to extend, we implemented the library using type annotation, which is a feature of Python 3.5 and later versions. This feature allows us to specify the type of the parameters and the return of the functions, making the code more readable and easier to understand.

Another feature of python that made us choose this language was the easy manipulation of raw bytes, which is necessary for the cryptographic operations.

Testing the library was done using the shell and python scripts. The tests were done to ensure that the library was working as expected and that the cryptographic operations were being done correctly. These can be found in the `tests` folder, and an explanation on how to run them can be found in the [`README.md`](./test/README.md) file.

The main functions of the library are:

- `protect`: This function takes a JSON document, a, the target fields and an output path as input and writes the protected document to the output path.
- `unprotect`: This function takes a protected document, a key, the target fields and an output path as input and writes the unprotected document to the output path.
- `check`: This function takes a protected document, a key and the target fields as input and returns a boolean indicating if the document is valid or not.
- `sign_data` and `verify_data`: These functions are used to sign and verify the signatures.

The `protect`, `unprotect` and `check` functions are the available to be used as a terminal command. The usage of these commands can be found in the [`README.md`](./src/cryptolib/README.md) file.

@girao nao falo aqui sobre o PKI, e com o ultimo commit que fizeste hj dia 30 nao sei se o sign_data e verify_data ainda existem da mesma forma que descrevo em cima. Pff checka e completa com os metodos que achares necessarios.

## 2.3 Infrastructure

NixOS, firewalls, certs, cas, firewalls, Secure Server Communication (TLS), etc. @girao

## 2.4 Threat Model

One of the assumptions we made in our threat model is that the attacker has the capability to intercept network traffic and send malicious requests, but we assume that the attacker cannot compromise the actual machines.

We also assume that the keys used in the cryptographic operations are secure and were securely distributed. @girao aqui elas sao distribuidas ou é CA stuff?

If private keys are compromised, the attacker can impersonate the entity that owns the key.

If the certificate authority (CA) is compromised, the attacker can issue certificates for any entity, which can be used to impersonate that entity.

## 2.5 Protection needs and Security Challenges Response

In this section, we will explain how we addressed the specific protection needs and security challenges that were defined in the beginning of the project.

### 2.5.1. \[SR1: Confidentiality\] The car configurations can only be seen by the car owner.

To ensure that the car configurations can only be seen by the car owner, we used the `cryptolib` library to protect the documents that are sent to the car. This library encrypts the document using the ChaCha20Poly1305 algorithm, which will use the car owner's private key to encrypt the document. This way, only the car owner can decrypt the document and see the configurations.

### 2.5.2. \[SR2: Integrity 1\] The car can only accept configurations sent by the car owner.

ainda nao fizemos isto mas tenho ideias q é CA stuff

### 2.5.3. \[SR3: Integrity 2\] The car firmware updates can only be sent by the car manufacturer.

ainda nao fizemos isto mas tenho ideias q é CA stuff

### 2.5.4. \[SR4: Authentication\] The car manufacture cannot deny having sent firmware updates.

In order to ensure that the car manufacturer cannot deny having sent firmware updates, we used the `cryptolib` library to sign the firmware that is sent to the car. This library signs the firmware using the car manufacturer's private key, which will be verified by the car using the car manufacturer's public key. This way, the car can verify that the document was indeed sent by the car manufacturer.

### 2.5.5. \[SRB1: data privacy\] The mechanic cannot see the user configurations, even when he has the car key.

ainda nao fizemos isto e sinceramente ainda nao sei como isto vai ser feito

### 2.5.6. \[SRB2: authorization\] The mechanic (when authenticated) can change any parameter of the car, for testing purposes.

ainda nao fizemos isto mas tem a ver com o modo de manutenção que que e ativado pelo car owner quando ele vai ao mecânico

### 2.5.7. \[SRB3: data authenticity\] The user can verify that the mechanic performed all the tests to the car.

Ainda nao fizemos mas probably vamos fazer como fazemos para o manufacturer ser verificavel de ter enviado o firmware

## 3. Conclusion

With the implementation of the MotorIST project, we were able to achieve the protection goals and security challenges that were defined in the beginning of the project. The custom cryptographic library that we implemented, `cryptolib`, was a key part of the project, as it allowed us to protect, verify and unprotect the documents that are sent to the car. This library was implemented using the Python programming language, which allowed us to easily integrate it with the rest of the project.

\[falar sobre o que pode ser melhorado\] @girao podes dar sugestões aqui?

There are still some features and improvements that could be made to the project. For example, we could implement a web interface for the car owner to manage the car configurations, which would make it easier for the car owner to interact with the car by having a better UI/UX.

Another improvement that could be made is to implement support for multiple entities, such as multiple car owners, mechanics and car manufacturers. This would allow the project to be more flexible and to better mimic a real-world scenario.

\[falar sobre o que pode ser melhorado\]

This project was a great opportunity to learn more about security and cryptography, and we are very happy with the results that we achieved. The infrastructure that we implemented was also a great learning experience, as we had to deal with firewalls, certificates, CAs and other security mechanisms for the first tine.

To conclude, we are very happy with the results that we achieved in this project, and we are confident that the MotorIST project is secure and ready to be used by the users.

# References

- "Subject Alternative Name" (SAN) - https://datatracker.ietf.org/doc/html/rfc5280#section-4.2.1.6
- "Everything you should know about certificates and PKI but are too afraid to ask" - https://smallstep.com/blog/everything-pki/
- "X.509 Verification" - https://cryptography.io/en/latest/x509/verification/
- "ChaCha20Poly1305" - https://en.wikipedia.org/wiki/ChaCha20-Poly1305
- "Authenticated Encryption with Associated Data" - https://en.wikipedia.org/wiki/Authenticated_encryption
- "ChaCha20Poly1305 on IoT devices" - https://ieeexplore.ieee.org/document/7927078
