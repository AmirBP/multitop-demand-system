import { DEMO_MODE } from "./DataSource";
import { ApiDataSource } from "./ApiDataSource";
import { MockDataSource } from "./MockDataSource";

export const dataSource = DEMO_MODE ? new MockDataSource() : new ApiDataSource();
