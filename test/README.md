# Tests

## 1. [TEST] Protect, Unprotect and Check

### 1.1 Setup

### 1.2 Running the tests

## 2. [TEST] Sign and Verify

### 2.1 Setup
In order to run the tests, you need to have the manufacturer private key public key. You can generate them by running the following commands:

```bash
./key-gen.sh 1
```

This will generate the manufacturer's private key and public key in the `keys` folder.

It is also necessary to run a manufacturer server that will issue the firmware. You can do this by running the following command on the `src/manufacturer` folder:

```bash
python3 main.py 1
```

### 2.2 Running the tests
to run the tests, you need to run the following command:

```bash
python3 verify_signature_test.py
```