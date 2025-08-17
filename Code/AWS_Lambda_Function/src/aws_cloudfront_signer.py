import base64

class CloudFrontSigner:
    def __init__(self, key_id, rsa_signer):
        self.key_id = key_id
        self.rsa_signer = rsa_signer

    def _encode(self, data: bytes) -> str:
        b64 = base64.b64encode(data).decode('utf-8')
        return b64.replace('+', '-').replace('=', '_').replace('/', '~')

    def generate_cookie(self, policy: str) -> dict:
        policy_bytes = policy.encode('utf-8')
        signature    = self.rsa_signer(policy_bytes)
        return {
          'CloudFront-Policy':     self._encode(policy_bytes),
          'CloudFront-Signature':  self._encode(signature),
          'CloudFront-Key-Pair-Id': self.key_id
        }