create table service (
    rid varchar(30) UNIQUE NOT NULL,
    uid varchar(10) UNIQUE NOT NULL,
    ts TIMESTAMP NOT NULL,
    PRIMARY KEY(rid)
);
create table service_update (
    update_id varchar(30) PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    rid varchar(30) NOT NULL,
    CONSTRAINT service_rid
        FOREIGN KEY(rid) 
        REFERENCES service(rid)
);
create table timestamp (
    ts_id varchar(30) UNIQUE NOT NULL,
    ts TIMESTAMP NOT NULL,
    src varchar(30),
    delayed BOOLEAN,
    status varchar(30),
    PRIMARY KEY(ts_id)
);
create table platform (
    plat_id varchar(30) UNIQUE NOT NULL,
    src varchar(30),
    confirmed BOOLEAN,
    text varchar(30),
    PRIMARY KEY(plat_id)
);
create table location (
    loc_id varchar(30) UNIQUE NOT NULL,
    toc varchar(10) NOT NULL,
    departure_id varchar(30) UNIQUE,
    arrival_id varchar(30) UNIQUE,
    platform_id varchar(30) UNIQUE,
    PRIMARY KEY(loc_id),
    CONSTRAINT departure_ts
        FOREIGN KEY(departure_id) 
        REFERENCES timestamp(ts_id),
    CONSTRAINT arrival_ts
        FOREIGN KEY(arrival_id) 
        REFERENCES timestamp(ts_id),
    CONSTRAINT platform_id
        FOREIGN KEY(platform_id) 
        REFERENCES platform(plat_id)
);