FROM freeradius/freeradius-server:3.2.10
RUN find /etc/freeradius/mods-enabled -mindepth 1 -maxdepth 1 -exec rm -f {} + \
    && ln -s ../mods-available/pap /etc/freeradius/mods-enabled/pap \
    && ln -s ../mods-available/expr /etc/freeradius/mods-enabled/expr \
    && ln -s ../mods-available/always /etc/freeradius/mods-enabled/always \
    && rm -f /etc/freeradius/sites-enabled/default /etc/freeradius/sites-enabled/inner-tunnel
COPY --chown=freerad:freerad freeradius/mods-enabled/sql /etc/freeradius/mods-enabled/sql
COPY --chown=freerad:freerad freeradius/sites-enabled/sol-pppoe /etc/freeradius/sites-enabled/sol-pppoe
COPY --chown=freerad:freerad freeradius/clients.conf /etc/freeradius/clients.conf
CMD ["freeradius", "-f"]
