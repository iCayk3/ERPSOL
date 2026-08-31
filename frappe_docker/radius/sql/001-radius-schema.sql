CREATE TABLE IF NOT EXISTS radcheck (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, username VARCHAR(64) NOT NULL DEFAULT '',
  attribute VARCHAR(64) NOT NULL DEFAULT '', op CHAR(2) NOT NULL DEFAULT ':=', value VARCHAR(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id), KEY idx_radcheck_username (username)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radreply (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, username VARCHAR(64) NOT NULL DEFAULT '',
  attribute VARCHAR(64) NOT NULL DEFAULT '', op CHAR(2) NOT NULL DEFAULT ':=', value VARCHAR(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id), KEY idx_radreply_username (username)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radgroupcheck (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, groupname VARCHAR(64) NOT NULL DEFAULT '',
  attribute VARCHAR(64) NOT NULL DEFAULT '', op CHAR(2) NOT NULL DEFAULT ':=', value VARCHAR(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id), KEY idx_groupcheck (groupname)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radgroupreply (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, groupname VARCHAR(64) NOT NULL DEFAULT '',
  attribute VARCHAR(64) NOT NULL DEFAULT '', op CHAR(2) NOT NULL DEFAULT ':=', value VARCHAR(253) NOT NULL DEFAULT '',
  PRIMARY KEY (id), KEY idx_groupreply (groupname)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radusergroup (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, username VARCHAR(64) NOT NULL DEFAULT '',
  groupname VARCHAR(64) NOT NULL DEFAULT '', priority INT NOT NULL DEFAULT 1,
  PRIMARY KEY (id), KEY idx_usergroup_username (username)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radacct (
  radacctid BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, acctsessionid VARCHAR(64) NOT NULL DEFAULT '',
  acctuniqueid VARCHAR(32) NOT NULL DEFAULT '', username VARCHAR(64) NOT NULL DEFAULT '', realm VARCHAR(64) DEFAULT '',
  nasipaddress VARCHAR(45) NOT NULL DEFAULT '', nasportid VARCHAR(32) DEFAULT NULL, nasporttype VARCHAR(32) DEFAULT NULL,
  acctstarttime DATETIME DEFAULT NULL, acctupdatetime DATETIME DEFAULT NULL, acctstoptime DATETIME DEFAULT NULL,
  acctinterval INT DEFAULT NULL, acctsessiontime INT UNSIGNED DEFAULT NULL, acctauthentic VARCHAR(32) DEFAULT NULL,
  connectinfo_start VARCHAR(128) DEFAULT NULL, connectinfo_stop VARCHAR(128) DEFAULT NULL,
  acctinputoctets BIGINT DEFAULT NULL, acctoutputoctets BIGINT DEFAULT NULL,
  calledstationid VARCHAR(50) NOT NULL DEFAULT '', callingstationid VARCHAR(50) NOT NULL DEFAULT '',
  acctterminatecause VARCHAR(32) NOT NULL DEFAULT '', servicetype VARCHAR(32) DEFAULT NULL,
  framedprotocol VARCHAR(32) DEFAULT NULL, framedipaddress VARCHAR(45) NOT NULL DEFAULT '',
  framedipv6address VARCHAR(45) NOT NULL DEFAULT '', framedipv6prefix VARCHAR(45) NOT NULL DEFAULT '',
  framedinterfaceid VARCHAR(44) NOT NULL DEFAULT '', delegatedipv6prefix VARCHAR(45) NOT NULL DEFAULT '',
  class VARCHAR(64) DEFAULT NULL,
  PRIMARY KEY (radacctid), UNIQUE KEY idx_radacct_unique (acctuniqueid),
  KEY idx_radacct_user (username), KEY idx_radacct_active (acctstoptime), KEY idx_radacct_session (acctsessionid)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS radpostauth (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, username VARCHAR(64) NOT NULL DEFAULT '',
  pass VARCHAR(64) NOT NULL DEFAULT '', reply VARCHAR(32) NOT NULL DEFAULT '', authdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  class VARCHAR(64) DEFAULT NULL, PRIMARY KEY (id), KEY idx_postauth_user (username)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nas (
  id INT NOT NULL AUTO_INCREMENT, nasname VARCHAR(128) NOT NULL, shortname VARCHAR(32), type VARCHAR(30) DEFAULT 'other',
  ports INT, secret VARCHAR(253) NOT NULL, server VARCHAR(64), community VARCHAR(50), description VARCHAR(200),
  PRIMARY KEY (id), UNIQUE KEY uq_nasname (nasname)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS nasreload (
  nasipaddress VARCHAR(45) NOT NULL, reloadtime DATETIME NOT NULL,
  PRIMARY KEY (nasipaddress)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS sol_radius_sync (
  source_doctype VARCHAR(64) NOT NULL, source_name VARCHAR(140) NOT NULL, username VARCHAR(64) NOT NULL,
  version INT UNSIGNED NOT NULL, enabled TINYINT(1) NOT NULL DEFAULT 0, payload_hash CHAR(64) NOT NULL,
  synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (source_doctype, source_name), UNIQUE KEY uq_sync_username (username)
) ENGINE=InnoDB;
