import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '10s',
};

export default function () {
  http.get("http://192.168.109.254:31320/gaphio/v1/raw-data");
  sleep(1);
}

export function handleSummary(data) {
  return { "/var/folders/dq/0lq2_dks2z717ybs4__0k7rw0000gn/T/k6_summary_xdpl0f5k.json": JSON.stringify(data) };
}