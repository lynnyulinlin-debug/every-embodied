const inventory = [
  { name: "纸巾", quantity: 2, threshold: 3, location: "客厅柜" },
  { name: "洗手液", quantity: 1, threshold: 1, location: "卫生间" },
  { name: "电池", quantity: 8, threshold: 4, location: "工具箱" },
];

const list = document.querySelector("[data-inventory-list]");

for (const item of inventory) {
  const row = document.createElement("li");
  const lowStock = item.quantity <= item.threshold;
  row.textContent = `${item.name}：${item.quantity} 件，位置：${item.location}`;
  row.dataset.status = lowStock ? "low" : "ok";
  list.append(row);
}
