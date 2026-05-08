FROM odoo:17.0

USER root

# Fix pyOpenSSL/cryptography/urllib3 version conflicts in the Odoo 17 base image
RUN pip3 install --no-cache-dir \
    "cryptography==41.0.7" \
    "pyOpenSSL==23.3.0" \
    "urllib3==1.26.18" \
    firebase-admin \
    pyfcm

# Create addons directory
RUN mkdir -p /mnt/extra-addons

# Copy custom addons
COPY ./multi_vendor_App /mnt/extra-addons/

# Fix permissions
RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
