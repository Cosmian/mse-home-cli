"""mse_home.model.evidence module."""

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional, cast

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_public_key,
)
from cryptography.x509 import (
    Certificate,
    CertificateRevocationList,
    load_pem_x509_certificate,
    load_pem_x509_crl,
)
from mse_cli_core.no_sgx_docker import NoSgxDockerConfig
from pydantic import BaseModel


class Collaterals(BaseModel):
    """Definition of collaterals."""

    root_ca_crl: CertificateRevocationList
    pck_platform_crl: CertificateRevocationList
    tcb_info: bytes
    qe_identity: bytes
    tcb_cert: Certificate

    class Config:
        """Overwrite internal structure."""

        arbitrary_types_allowed = True


class ApplicationEvidence(BaseModel):
    """Definition of an enclave evidence."""

    ratls_certificate: Certificate
    collaterals: Optional[Collaterals]
    signer_pk: RSAPublicKey
    input_args: NoSgxDockerConfig

    class Config:
        """Overwrite internal structure."""

        arbitrary_types_allowed = True

    @staticmethod
    def load(path: Path):
        """Load the evidence from a json file."""
        with open(path, encoding="utf8") as f:
            data_map = json.load(f)

            collaterals: Optional[Collaterals] = None

            if "collaterals" in data_map and data_map["collaterals"]:
                collaterals = Collaterals(
                    root_ca_crl=load_pem_x509_crl(
                        data_map["collaterals"]["root_ca_crl"].encode("utf-8")
                    ),
                    pck_platform_crl=load_pem_x509_crl(
                        data_map["collaterals"]["pck_platform_crl"].encode("utf-8")
                    ),
                    tcb_info=base64.b64decode(
                        data_map["collaterals"]["tcb_info"].encode("utf-8")
                    ),
                    qe_identity=base64.b64decode(
                        data_map["collaterals"]["qe_identity"].encode("utf-8")
                    ),
                    tcb_cert=load_pem_x509_certificate(
                        data_map["collaterals"]["tcb_cert"].encode("utf-8")
                    ),
                )
            signer_pk = load_pem_public_key(data_map["signer_pk"].encode("utf-8"))

            if not isinstance(signer_pk, RSAPublicKey):
                raise Exception("Signer public key is not an RSA public key!")

            return ApplicationEvidence(
                input_args=NoSgxDockerConfig(**data_map["input_args"]),
                ratls_certificate=load_pem_x509_certificate(
                    data_map["ratls_certificate"].encode("utf-8")
                ),
                collaterals=collaterals,
                signer_pk=cast(RSAPublicKey, signer_pk),
            )

    def save(self, path: Path) -> None:
        """Save the evidence into a json file."""
        with open(path, "w", encoding="utf8") as f:
            collaterals: Optional[Dict[str, Any]] = None

            if self.collaterals:
                collaterals = {
                    "root_ca_crl": self.collaterals.root_ca_crl.public_bytes(
                        encoding=Encoding.PEM,
                    ).decode("utf-8"),
                    "pck_platform_crl": self.collaterals.pck_platform_crl.public_bytes(
                        encoding=Encoding.PEM,
                    ).decode("utf-8"),
                    "tcb_info": base64.b64encode(self.collaterals.tcb_info).decode(
                        "utf-8"
                    ),
                    "qe_identity": base64.b64encode(
                        self.collaterals.qe_identity
                    ).decode("utf-8"),
                    "tcb_cert": self.collaterals.tcb_cert.public_bytes(
                        encoding=Encoding.PEM
                    ).decode("utf-8"),
                }

            data_map: Dict[str, Any] = {
                "input_args": {
                    "subject": self.input_args.subject,
                    "subject_alternative_name": self.input_args.subject_alternative_name,
                    "expiration_date": self.input_args.expiration_date
                    if self.input_args.expiration_date
                    else None,
                    "size": self.input_args.size,
                    "app_id": str(self.input_args.app_id),
                    "application": self.input_args.application,
                },
                "ratls_certificate": self.ratls_certificate.public_bytes(
                    encoding=Encoding.PEM
                ).decode("utf-8"),
                "collaterals": collaterals,
                "signer_pk": self.signer_pk.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo,
                ).decode("utf-8"),
            }

            json.dump(data_map, f, indent=4)
